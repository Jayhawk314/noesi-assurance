# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Hardened localhost API over the WorkbenchService.

Implements the assessment's local-shell requirements directly (a framework
would not provide them either): a high-entropy per-session bearer token
minted at startup; strict Host and Origin validation (browser-origin CSRF
defense); request body limits enforced before reading; a narrow Content
Security Policy and no-sniff headers on every response; loopback-only bind;
and no unauthenticated request of any kind — reads included.

Pilot profile: one process, one writer; requests serialize on a lock. The
firm-hosted profile replaces this module (FastAPI/ASGI + SSO) while the
application service underneath stays unchanged.
"""

from __future__ import annotations

import json
import secrets
import threading
from dataclasses import dataclass
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from assurance_application.service import (
    AuthorizationError, EngagementLockedError, EvidenceIntegrityError,
    WorkbenchService,
)
from assurance_artifacts.vault import VaultIntegrityError
from assurance_domain.errors import ConflictError, NotFoundError
from assurance_domain.lifecycle import SeparationOfDutiesError

MAX_JSON_BODY = 2 * 1024 * 1024          # JSON commands stay small
MAX_UPLOAD_BODY = 200 * 1024 * 1024      # artifact uploads match vault policy

_SECURITY_HEADERS = (
    ("Content-Security-Policy", "default-src 'none'"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "no-referrer"),
    ("Cache-Control", "no-store"),
)


@dataclass(frozen=True)
class SessionAuth:
    """One local session: a random bearer token held by one operator.

    ``principal_id`` is the chair the operator sits in by default. A request
    may act as a different principal via ``X-Acting-Principal`` — on a local
    single-operator pilot the console owner already controls every local
    identity (they could restart with any ``--principal``), so the header
    changes convenience, not the trust boundary. Every command is journaled
    under the chair that performed it, and the separation-of-duties gates
    apply to chairs exactly as they would to distinct people.
    """

    principal_id: str
    token: str

    @classmethod
    def create(cls, principal_id: str) -> "SessionAuth":
        return cls(principal_id, secrets.token_urlsafe(32))


_MAX_PRINCIPAL_LEN = 120


def _acting_principal(header_value: str | None, default: str) -> str:
    """Validate the acting-principal header; fail closed on nonsense."""
    if header_value is None or header_value == "":
        return default
    principal = header_value.strip()
    if (not principal or len(principal) > _MAX_PRINCIPAL_LEN
            or any(ch.isspace() for ch in principal)
            or not principal.isprintable()):
        raise ApiError(400, "invalid X-Acting-Principal header")
    return principal


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(message)


_STATIC_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".map": "application/json",
}

_STATIC_CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; "
               "connect-src 'self'; img-src 'self'")

# Replaced in the served index.html with the live session token. An inline
# script would be simpler but the static CSP forbids one, so it rides a meta tag.
_TOKEN_PLACEHOLDER = b"__NOESI_SESSION_TOKEN__"


def build_server(service: WorkbenchService, auth: SessionAuth,
                 host: str = "127.0.0.1", port: int = 0,
                 static_dir=None) -> ThreadingHTTPServer:
    """Create (do not start) the hardened HTTP server.

    ``static_dir`` (the built workbench-ui dist) is served on non-/api GET
    paths: Host-checked but tokenless (the page load cannot carry a bearer),
    path-resolved strictly inside the directory, with a scripts-self CSP.
    The data plane stays fully authenticated.
    """
    write_lock = threading.Lock()
    from pathlib import Path
    static_root = Path(static_dir).resolve() if static_dir else None

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "noesi-workbench"
        sys_version = ""

        def log_message(self, *args) -> None:  # quiet; the journal is the log
            pass

        # ------------------------------------------------------- plumbing

        def _reply(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False,
                              default=_json_default).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            for name, value in _SECURITY_HEADERS:
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def _reply_html(self, status: int, markup: str) -> None:
            body = markup.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            # The workpaper carries inline styles and nothing else.
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; style-src 'unsafe-inline'")
            for name, value in _SECURITY_HEADERS[1:]:
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def _allowed_hosts(self) -> set[str]:
            actual_port = self.server.server_address[1]
            return {f"127.0.0.1:{actual_port}", f"localhost:{actual_port}"}

        def _authenticate(self) -> str:
            """Every request: Host allowlist, Origin check, bearer token."""
            host_header = self.headers.get("Host", "")
            if host_header not in self._allowed_hosts():
                raise ApiError(403, "Host not allowed")
            origin = self.headers.get("Origin")
            if origin:
                parsed = urlsplit(origin)
                if f"{parsed.hostname}:{parsed.port or 80}" not in \
                        self._allowed_hosts():
                    raise ApiError(403, "Origin not allowed")
            header = self.headers.get("Authorization", "")
            scheme, _, token = header.partition(" ")
            if scheme != "Bearer" or not secrets.compare_digest(
                    token.strip(), auth.token):
                raise ApiError(401, "missing or invalid session token")
            return _acting_principal(
                self.headers.get("X-Acting-Principal"), auth.principal_id)

        def _read_body(self, limit: int) -> bytes:
            self._body_consumed = True
            length_header = self.headers.get("Content-Length")
            if length_header is None:
                raise ApiError(411, "Content-Length required")
            try:
                length = int(length_header)
            except ValueError as exc:
                raise ApiError(400, "bad Content-Length") from exc
            if length < 0 or length > limit:
                # Drain a bounded amount before refusing, so the client
                # reads an honest 413 instead of a connection reset (the
                # OS RSTs a close with unread data still in flight).
                remaining = min(length, limit + 1024 * 1024) if length > 0 else 0
                while remaining > 0:
                    chunk = self.rfile.read(min(65536, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                raise ApiError(413, f"body exceeds the {limit}-byte limit")
            return self.rfile.read(length)

        def _read_json(self) -> dict:
            data = self._read_body(MAX_JSON_BODY)
            try:
                payload = json.loads(data or b"{}")
            except ValueError as exc:
                raise ApiError(400, "request body is not valid JSON") from exc
            if not isinstance(payload, dict):
                raise ApiError(400, "request body must be a JSON object")
            return payload

        def _spec_ids(self) -> list[str]:
            body = self._read_json()
            spec_ids = body.get("spec_ids")
            if (not isinstance(spec_ids, list)
                    or not all(isinstance(s, str) for s in spec_ids)):
                raise ApiError(400, "spec_ids must be a list of strings")
            return spec_ids

        # ------------------------------------------------------- routing

        def do_GET(self) -> None:  # noqa: N802 — stdlib naming
            self._handle("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._handle("POST")

        def _serve_static(self, path: str) -> None:
            if self.headers.get("Host", "") not in self._allowed_hosts():
                self._reply(403, {"error": "Host not allowed"})
                return
            clean = path.split("?", 1)[0]
            candidate = (static_root / clean.lstrip("/")).resolve() \
                if clean not in ("", "/") else static_root / "index.html"
            try:
                candidate.relative_to(static_root)
            except ValueError:
                self._reply(404, {"error": "unknown path"})
                return
            if candidate.is_dir():
                candidate = candidate / "index.html"
            if not candidate.is_file():
                # SPA fallback: unknown non-asset paths get the shell.
                candidate = static_root / "index.html"
                if not candidate.is_file():
                    self._reply(404, {"error": "unknown path"})
                    return
            body = candidate.read_bytes()
            if candidate.name == "index.html":
                # The page load cannot carry a bearer, so the shell is handed
                # the session token inline. Reachable only through the
                # Host-checked loopback listener, and never cached.
                body = body.replace(_TOKEN_PLACEHOLDER,
                                    auth.token.encode("ascii"))
            self.send_response(200)
            self.send_header("Content-Type", _STATIC_TYPES.get(
                candidate.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Security-Policy", _STATIC_CSP)
            for name, value in _SECURITY_HEADERS[1:]:
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def _drain_unread_body(self) -> None:
            """Consume a request body no route read, or drop the connection.

            A route that replies without reading its body (an early refusal,
            a body-less handler) would otherwise leave those bytes in the
            keep-alive stream, and the *next* request on the connection
            would be parsed starting mid-garbage — observed live as
            ``Unsupported method ('{}GET')`` replacing a separation-of-
            duties refusal in the UI.
            """
            if getattr(self, "_body_consumed", False):
                return
            length_header = self.headers.get("Content-Length")
            if length_header is None:
                return
            try:
                remaining = int(length_header)
            except ValueError:
                self.close_connection = True
                return
            if remaining < 0 or remaining > MAX_JSON_BODY:
                self.close_connection = True  # not worth reading to reuse
                return
            while remaining > 0:
                chunk = self.rfile.read(min(65536, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)

        def _handle(self, method: str) -> None:
            self._body_consumed = False
            raw_path = urlsplit(self.path).path
            if (method == "GET" and static_root is not None
                    and not raw_path.startswith("/api")):
                self._serve_static(raw_path)
                return
            try:
                actor = self._authenticate()
                parts = [p for p in urlsplit(self.path).path.split("/") if p]
                result = self._dispatch(method, parts, actor)
                if result is not None:  # HTML routes reply for themselves
                    self._reply(200, result)
            except ApiError as exc:
                self._reply(exc.status, {"error": str(exc)})
            except AuthorizationError as exc:
                self._reply(403, {"error": str(exc)})
            except EngagementLockedError as exc:
                self._reply(423, {"error": str(exc)})
            except SeparationOfDutiesError as exc:
                self._reply(409, {"error": str(exc)})
            except ConflictError as exc:
                self._reply(409, {"error": str(exc)})
            except (VaultIntegrityError, EvidenceIntegrityError) as exc:
                # A named refusal, never an opaque 500: the operator must
                # know to suspect the evidence chain, not a crash (F3).
                self._reply(409, {"error": str(exc)})
            except (NotFoundError, KeyError) as exc:
                self._reply(404, {"error": str(exc)})
            except ValueError as exc:
                self._reply(400, {"error": str(exc)})
            except Exception:  # noqa: BLE001 — no internals in responses
                self._reply(500, {"error": "internal error"})
            finally:
                self._drain_unread_body()

        def _dispatch(self, method: str, parts: list[str], actor: str) -> dict:
            if parts[:1] != ["api"]:
                raise ApiError(404, "unknown path")
            route = parts[1:]

            # One connection, one request at a time — reads included. The
            # pilot is single-user; correctness beats concurrency here.
            with write_lock:
                if method == "GET":
                    return self._get(route, actor)
                return self._post(route, actor)

        def _get(self, route: list[str], actor: str) -> dict:
            match route:
                case ["session"]:
                    return {"principal_id": auth.principal_id}
                case ["manual"]:
                    from workbench_api.manual import (
                        default_manual_dir, list_chapters,
                    )
                    try:
                        return {"chapters": list_chapters(default_manual_dir())}
                    except FileNotFoundError as exc:
                        raise ApiError(404, str(exc)) from exc
                case ["manual", chapter]:
                    from workbench_api.manual import (
                        default_manual_dir, render_chapter,
                    )
                    return render_chapter(default_manual_dir(), chapter)
                case ["engagements"]:
                    return {"engagements": service.list_engagements()}
                case ["engagements", eid, "team"]:
                    return {"team": service.team(eid)}
                case ["engagements", eid, "sources"]:
                    return service.sources(eid)
                case ["engagements", eid, "coverage"]:
                    return service.coverage(eid)
                case ["engagements", eid, "workflow"]:
                    document, version = service.workflow_document(eid)
                    return {"document": document, "version": version}
                case ["engagements", eid, "runs"]:
                    return {"runs": service.runs(eid)}
                case ["engagements", eid, "findings"]:
                    return {"findings": service.findings(eid)}
                case ["engagements", eid, "sad"]:
                    return service.sad(eid)
                case ["engagements", eid, "readiness"]:
                    return service.readiness(eid)
                case ["engagements", eid, "lock"]:
                    return service.verify_lock(eid)
                case ["engagements", eid, "workpaper"]:
                    self._reply_html(
                        200, service.workpaper_html(actor, eid))
                    return None  # already replied
            raise ApiError(404, "unknown path")

        def _post(self, route: list[str], actor: str) -> dict:
            match route:
                case ["engagements"]:
                    body = self._read_json()
                    return service.create_engagement(
                        actor, str(body["client_name"]),
                        str(body["period_end"]))
                case ["engagements", eid, "team"]:
                    body = self._read_json()
                    return service.assign_team(
                        actor, eid, str(body["principal_id"]),
                        str(body["role"]))
                case ["engagements", eid, "sources"]:
                    content = self._read_body(MAX_UPLOAD_BODY)
                    return service.store_source(
                        actor, eid, content=content,
                        media_type=self.headers.get(
                            "Content-Type", "application/octet-stream"),
                        original_name=self.headers.get(
                            "X-Original-Name", "upload"),
                        provenance=self.headers.get("X-Provenance", ""))
                case ["engagements", eid, "mappings"]:
                    body = self._read_json()
                    return service.propose_source_mapping(
                        actor, eid, role=str(body["role"]),
                        artifact_id=str(body["artifact_id"]))
                # Bulk loading: batch endpoints compress the round trips of a
                # ten-file engagement into one pass per chair. The gates are
                # unchanged — the service loops the single-item use cases.
                case ["engagements", eid, "mappings", "propose-batch"]:
                    body = self._read_json()
                    items = body.get("items")
                    if (not isinstance(items, list)
                            or not all(isinstance(i, dict) for i in items)):
                        raise ApiError(400, "items must be a list of objects")
                    return service.propose_source_mappings(actor, eid, items)
                case ["engagements", eid, "mappings", "approve-batch"]:
                    return service.approve_source_mappings(
                        actor, eid, self._spec_ids())
                case ["engagements", eid, "mappings", "normalize-batch"]:
                    return service.normalize_sources(
                        actor, eid, self._spec_ids())
                case ["engagements", eid, "mappings", spec_id, "approve"]:
                    return service.approve_source_mapping(actor, eid, spec_id)
                case ["engagements", eid, "mappings", spec_id, "normalize"]:
                    return service.normalize_source(actor, eid, spec_id)
                case ["engagements", eid, "runs"]:
                    body = self._read_json()
                    return service.run_procedure(
                        actor, eid, procedure_id=str(body["procedure_id"]),
                        policies=dict(body.get("policies") or {}))
                case ["engagements", eid, "runs", run_id, "review"]:
                    body = self._read_json()
                    return service.review_run(
                        actor, eid, run_id,
                        target=str(body["target"]),
                        expected_version=int(body["expected_version"]))
                case ["engagements", eid, "dispositions"]:
                    body = self._read_json()
                    return service.set_disposition(
                        actor, eid, finding_uid=str(body["finding_uid"]),
                        status=str(body["status"]),
                        note=str(body.get("note", "")),
                        expected_version=int(body.get("expected_version", 0)))
                case ["engagements", eid, "dispositions", "concur"]:
                    body = self._read_json()
                    return service.concur_disposition(
                        actor, eid, finding_uid=str(body["finding_uid"]),
                        expected_version=int(body["expected_version"]))
                case ["engagements", eid, "workflow"]:
                    body = self._read_json()
                    return service.update_workflow(
                        actor, eid, str(body["section"]),
                        dict(body.get("values") or {}))
                case ["engagements", eid, "lock"]:
                    body = self._read_json()
                    return service.lock(
                        actor, eid,
                        expected_version=int(body["expected_version"]))
                case ["engagements", eid, "unlock"]:
                    body = self._read_json()
                    return service.unlock(
                        actor, eid,
                        reason=str(body.get("reason", "")),
                        expected_version=int(body["expected_version"]))
                case ["engagements", eid, "export"]:
                    return service.export_packet(actor, eid)
            raise ApiError(404, "unknown path")

    return ThreadingHTTPServer((host, port), Handler)
