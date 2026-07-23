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
    AuthorizationError, EngagementLockedError, WorkbenchService,
)
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
    """One local session: a random bearer token bound to one principal."""

    principal_id: str
    token: str

    @classmethod
    def create(cls, principal_id: str) -> "SessionAuth":
        return cls(principal_id, secrets.token_urlsafe(32))


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
            return auth.principal_id

        def _read_body(self, limit: int) -> bytes:
            length_header = self.headers.get("Content-Length")
            if length_header is None:
                raise ApiError(411, "Content-Length required")
            try:
                length = int(length_header)
            except ValueError as exc:
                raise ApiError(400, "bad Content-Length") from exc
            if length < 0 or length > limit:
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
            self.send_response(200)
            self.send_header("Content-Type", _STATIC_TYPES.get(
                candidate.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Security-Policy", _STATIC_CSP)
            for name, value in _SECURITY_HEADERS[1:]:
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def _handle(self, method: str) -> None:
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
            except (NotFoundError, KeyError) as exc:
                self._reply(404, {"error": str(exc)})
            except ValueError as exc:
                self._reply(400, {"error": str(exc)})
            except Exception:  # noqa: BLE001 — no internals in responses
                self._reply(500, {"error": "internal error"})

        def _dispatch(self, method: str, parts: list[str], actor: str) -> dict:
            if parts[:1] != ["api"]:
                raise ApiError(404, "unknown path")
            route = parts[1:]

            # One connection, one request at a time — reads included. The
            # pilot is single-user; correctness beats concurrency here.
            with write_lock:
                if method == "GET":
                    return self._get(route)
                return self._post(route, actor)

        def _get(self, route: list[str]) -> dict:
            match route:
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
                        200, service.workpaper_html(auth.principal_id, eid))
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
                case ["engagements", eid, "export"]:
                    return service.export_packet(actor, eid)
            raise ApiError(404, "unknown path")

    return ThreadingHTTPServer((host, port), Handler)
