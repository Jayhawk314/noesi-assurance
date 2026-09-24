# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The hardened boundary: every request authenticated, origins policed,
bodies limited, and the six screens reachable over HTTP."""

import http.client
import json
import threading

import pytest

from assurance_application.service import WorkbenchService
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant
from workbench_api.server import SessionAuth, build_server

PAYMENTS_CSV = (
    "Payment No,Invoice No,Vendor No,Amount,Payment Date\n"
    "P1,I1,V1,6000.00,2025-03-01\n"
    "P2,I2,V1,5000.00,2025-03-01\n"
).encode("utf-8")


@pytest.fixture()
def api(tmp_path):
    conn = connect(tmp_path / "control.db", allow_cross_thread=True)
    migrate(conn)
    tenant = ensure_tenant(conn, "firm")
    service = WorkbenchService(conn, ArtifactVault(tmp_path / "vault"), tenant)
    auth = SessionAuth.create("principal-alice")
    static = tmp_path / "dist"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text(
        "<!doctype html><title>workbench</title>", encoding="utf-8")
    (static / "assets" / "app.js").write_text("console.log('ui')",
                                              encoding="utf-8")
    studio = tmp_path / "studio"
    (studio / "assets").mkdir(parents=True)
    (studio / "index.html").write_text(
        '<!doctype html><title>studio</title>'
        '<meta name="noesi-session" content="__NOESI_SESSION_TOKEN__">',
        encoding="utf-8")
    (studio / "assets" / "studio.js").write_text("console.log('studio')",
                                                 encoding="utf-8")
    (studio / "videos").mkdir()
    (studio / "videos" / "lesson.mp4").write_bytes(bytes(range(256)) * 4)  # 1024 bytes
    server = build_server(service, auth, port=0, static_dir=static,
                          studio_dir=studio)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server.server_address[1], auth
    server.shutdown()
    server.server_close()
    conn.close()


def _request(port, method, path, *, token=None, body=None, headers=None,
             raw_body=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    all_headers = dict(headers or {})
    if token:
        all_headers["Authorization"] = f"Bearer {token}"
    payload = raw_body if raw_body is not None else (
        json.dumps(body).encode("utf-8") if body is not None else None)
    if payload is not None:
        all_headers.setdefault("Content-Type", "application/json")
    conn.request(method, path, body=payload, headers=all_headers)
    response = conn.getresponse()
    data = json.loads(response.read() or b"{}")
    conn.close()
    return response.status, data


# ------------------------------------------------------------- hardening

def test_requests_without_a_token_are_rejected_reads_included(api):
    port, _ = api
    status, body = _request(port, "GET", "/api/engagements")
    assert status == 401
    status, _ = _request(port, "GET", "/api/engagements", token="forged")
    assert status == 401


def test_wrong_host_header_is_rejected(api):
    port, auth = api
    status, _ = _request(port, "GET", "/api/engagements", token=auth.token,
                         headers={"Host": "evil.example.com"})
    assert status == 403


def test_cross_origin_browser_requests_are_rejected(api):
    port, auth = api
    status, _ = _request(port, "POST", "/api/engagements", token=auth.token,
                         body={"client_name": "Acme", "period_end": "2025"},
                         headers={"Origin": "https://evil.example.com"})
    assert status == 403
    # Same-origin requests pass.
    status, _ = _request(port, "GET", "/api/engagements", token=auth.token,
                         headers={"Origin": f"http://127.0.0.1:{port}"})
    assert status == 200


def test_oversize_json_bodies_are_refused(api):
    port, auth = api
    status, body = _request(
        port, "POST", "/api/engagements", token=auth.token,
        raw_body=b"x" * (2 * 1024 * 1024 + 1))
    assert status == 413


def test_responses_carry_security_headers(api):
    port, auth = api
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", "/api/engagements",
                 headers={"Authorization": f"Bearer {auth.token}"})
    response = conn.getresponse()
    response.read()
    assert response.getheader("Content-Security-Policy") == "default-src 'none'"
    assert response.getheader("X-Content-Type-Options") == "nosniff"
    assert response.getheader("X-Frame-Options") == "DENY"
    conn.close()


def test_ui_shell_is_served_without_a_token_but_host_checked(api):
    port, _ = api
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", "/")
    response = conn.getresponse()
    body = response.read().decode()
    assert response.status == 200
    assert "workbench" in body
    assert "script-src 'self'" in response.getheader("Content-Security-Policy")
    conn.close()

    status, _ = _request(port, "GET", "/",
                         headers={"Host": "evil.example.com"})
    assert status == 403


def test_studio_is_mounted_beside_the_workbench(api):
    port, auth = api
    for path in ("/studio", "/studio/", "/studio/engagement/x"):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        conn.request("GET", path)
        response = conn.getresponse()
        body = response.read().decode()
        assert response.status == 200, path
        assert "studio" in body and auth.token in body
        conn.close()
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", "/studio/assets/studio.js")
    response = conn.getresponse()
    assert "studio" in response.read().decode()
    conn.close()
    # Traversal out of the studio root never reaches the data directory.
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", "/studio/../control.db")
    assert b"SQLite" not in conn.getresponse().read()
    conn.close()
    status, _ = _request(port, "GET", "/studio/",
                         headers={"Host": "evil.example.com"})
    assert status == 403


def _get_raw(port, path, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", path, headers=headers or {})
    response = conn.getresponse()
    body = response.read()
    conn.close()
    return response, body


def test_lesson_videos_play_and_seek(api):
    port, _ = api
    response, body = _get_raw(port, "/studio/videos/lesson.mp4")
    assert response.status == 200 and len(body) == 1024
    assert response.getheader("Content-Type") == "video/mp4"
    assert response.getheader("Accept-Ranges") == "bytes"
    assert "media-src 'self'" in response.getheader("Content-Security-Policy")

    # A browser seeking inside the video asks for a byte range.
    response, body = _get_raw(port, "/studio/videos/lesson.mp4", {"Range": "bytes=100-199"})
    assert response.status == 206
    assert response.getheader("Content-Range") == "bytes 100-199/1024"
    assert body == (bytes(range(256)) * 4)[100:200]
    response, body = _get_raw(port, "/studio/videos/lesson.mp4", {"Range": "bytes=1000-"})
    assert response.status == 206 and len(body) == 24
    response, body = _get_raw(port, "/studio/videos/lesson.mp4", {"Range": "bytes=-10"})
    assert response.status == 206 and len(body) == 10
    response, _ = _get_raw(port, "/studio/videos/lesson.mp4", {"Range": "bytes=5000-"})
    assert response.status == 416


def test_static_assets_serve_and_traversal_is_contained(api):
    port, _ = api
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", "/assets/app.js")
    response = conn.getresponse()
    assert response.status == 200
    assert "javascript" in response.getheader("Content-Type")
    response.read()
    conn.close()

    # Traversal attempts resolve inside the static root or 404 — never
    # escape. (The SPA fallback may serve the shell; that is fine.)
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", "/assets/../../control.db")
    response = conn.getresponse()
    body = response.read()
    assert b"SQLite" not in body
    conn.close()

    # The data plane is untouched by the static allowance.
    status, _ = _request(port, "GET", "/api/engagements")
    assert status == 401


def test_unknown_paths_and_internal_errors_stay_opaque(api):
    port, auth = api
    status, _ = _request(port, "GET", "/api/secrets", token=auth.token)
    assert status == 404
    status, body = _request(port, "POST", "/api/engagements",
                            token=auth.token, body={"client_name": "X"})
    assert status in (400, 404, 500)
    assert "Traceback" not in json.dumps(body)


# ---------------------------------------------------------- the six screens

def test_full_engagement_journey_over_http(api):
    port, auth = api
    token = auth.token

    status, created = _request(
        port, "POST", "/api/engagements", token=token,
        body={"client_name": "Acme", "period_end": "2025-12-31"})
    assert status == 200
    eid = created["engagement_id"]

    # The session principal is the partner; assign themselves preparer +
    # reviewer roles is forbidden by separation later, so add a second
    # role only where the matrix allows single-user work.
    status, _ = _request(port, "POST", f"/api/engagements/{eid}/team",
                         token=token,
                         body={"principal_id": "principal-alice",
                               "role": "preparer"})
    assert status == 200

    status, artifact = _request(
        port, "POST", f"/api/engagements/{eid}/sources", token=token,
        raw_body=PAYMENTS_CSV,
        headers={"Content-Type": "text/csv",
                 "X-Original-Name": "payments.csv"})
    assert status == 200

    status, proposal = _request(
        port, "POST", f"/api/engagements/{eid}/mappings", token=token,
        body={"role": "Payments", "artifact_id": artifact["artifact_id"]})
    assert status == 200
    assert proposal["column_map"]["payment_number"] == "Payment No"

    # A proposal's author cannot approve it, whatever roles they hold — the
    # separation gates treat chairs as people.
    status, denied = _request(
        port, "POST",
        f"/api/engagements/{eid}/mappings/{proposal['spec_id']}/approve",
        token=token, body={})
    assert status == 403

    status, coverage = _request(port, "GET",
                                f"/api/engagements/{eid}/coverage",
                                token=token)
    assert status == 200
    assert coverage["summary"]["total"] == 11

    status, state = _request(port, "GET",
                             f"/api/engagements/{eid}/readiness", token=token)
    assert status == 200
    assert state["ready"] is False

    status, lock = _request(port, "POST", f"/api/engagements/{eid}/lock",
                            token=token, body={"expected_version": 1})
    assert status == 200
    assert lock["locked"] is False

    # Unlock is reachable and fails closed on an engagement never locked.
    status, body = _request(port, "POST", f"/api/engagements/{eid}/unlock",
                            token=token,
                            body={"reason": "A specific documented reason.",
                                  "expected_version": 1})
    assert status == 400
    assert "not locked" in body["error"]


# ---------------------------------------------------------- chair switching

def test_acting_principal_header_completes_the_review_loop(api):
    """One operator, several chairs: the loop that used to dead-end."""
    port, auth = api
    token = auth.token

    status, session = _request(port, "GET", "/api/session", token=token)
    assert status == 200
    assert session["principal_id"] == "principal-alice"

    _, created = _request(
        port, "POST", "/api/engagements", token=token,
        body={"client_name": "Acme", "period_end": "2025-12-31"})
    eid = created["engagement_id"]
    for principal, role in (("pat-preparer", "preparer"),
                            ("rae-reviewer", "reviewer")):
        status, _ = _request(port, "POST", f"/api/engagements/{eid}/team",
                             token=token,
                             body={"principal_id": principal, "role": role})
        assert status == 200

    as_pat = {"X-Acting-Principal": "pat-preparer"}
    as_rae = {"X-Acting-Principal": "rae-reviewer"}

    status, artifact = _request(
        port, "POST", f"/api/engagements/{eid}/sources", token=token,
        raw_body=PAYMENTS_CSV,
        headers={**as_pat, "Content-Type": "text/csv",
                 "X-Original-Name": "payments.csv"})
    assert status == 200
    status, proposal = _request(
        port, "POST", f"/api/engagements/{eid}/mappings", token=token,
        headers=as_pat,
        body={"role": "Payments", "artifact_id": artifact["artifact_id"]})
    assert status == 200

    # The preparer still cannot approve their own proposal…
    status, _ = _request(
        port, "POST",
        f"/api/engagements/{eid}/mappings/{proposal['spec_id']}/approve",
        token=token, headers=as_pat, body={})
    assert status == 403
    # …but the reviewer chair can, and the preparer then normalizes.
    status, _ = _request(
        port, "POST",
        f"/api/engagements/{eid}/mappings/{proposal['spec_id']}/approve",
        token=token, headers=as_rae, body={})
    assert status == 200
    status, normalized = _request(
        port, "POST",
        f"/api/engagements/{eid}/mappings/{proposal['spec_id']}/normalize",
        token=token, headers=as_pat, body={})
    assert status == 200
    assert normalized["reconciliation"]["rows_loaded"] == 2


def test_garbage_acting_principal_header_is_refused(api):
    port, auth = api
    for bad in ("two words", "x" * 121, "tab\there"):
        status, body = _request(
            port, "GET", "/api/engagements", token=auth.token,
            headers={"X-Acting-Principal": bad})
        assert status == 400, bad
        assert "X-Acting-Principal" in body["error"]


def test_batch_endpoints_bulk_load_in_one_pass_per_chair(api):
    """Ten round trips per file become three batch calls across the chairs."""
    port, auth = api
    token = auth.token

    _, created = _request(
        port, "POST", "/api/engagements", token=token,
        body={"client_name": "Acme", "period_end": "2025-12-31"})
    eid = created["engagement_id"]
    for principal, role in (("pat-preparer", "preparer"),
                            ("rae-reviewer", "reviewer")):
        _request(port, "POST", f"/api/engagements/{eid}/team", token=token,
                 body={"principal_id": principal, "role": role})
    as_pat = {"X-Acting-Principal": "pat-preparer"}
    as_rae = {"X-Acting-Principal": "rae-reviewer"}

    ids = []
    for name, payload in (("payments.csv", PAYMENTS_CSV),
                          ("ap_control_balance.csv",
                           b"Period End,Subledger Balance,GL Balance\n"
                           b"2025-12-31,1000.00,1000.00\n")):
        status, artifact = _request(
            port, "POST", f"/api/engagements/{eid}/sources", token=token,
            raw_body=payload,
            headers={**as_pat, "Content-Type": "text/csv",
                     "X-Original-Name": name})
        assert status == 200
        ids.append(artifact["artifact_id"])

    # Preparer pass: one call, roles inferred from the filenames.
    status, proposals = _request(
        port, "POST", f"/api/engagements/{eid}/mappings/propose-batch",
        token=token, headers=as_pat,
        body={"items": [{"artifact_id": aid} for aid in ids]})
    assert status == 200
    assert proposals["proposed"] == 2 and proposals["errors"] == 0
    spec_ids = [r["spec_id"] for r in proposals["results"]]

    # Reviewer pass; the proposing chair is refused outright.
    status, _ = _request(
        port, "POST", f"/api/engagements/{eid}/mappings/approve-batch",
        token=token, headers=as_pat, body={"spec_ids": spec_ids})
    assert status == 403
    status, approvals = _request(
        port, "POST", f"/api/engagements/{eid}/mappings/approve-batch",
        token=token, headers=as_rae, body={"spec_ids": spec_ids})
    assert status == 200
    assert approvals["approved"] == 2

    # Preparer pass: batch normalize closes the loop.
    status, normalized = _request(
        port, "POST", f"/api/engagements/{eid}/mappings/normalize-batch",
        token=token, headers=as_pat, body={"spec_ids": spec_ids})
    assert status == 200
    assert normalized["normalized"] == 2

    # Malformed batch bodies are refused before touching the service.
    status, body = _request(
        port, "POST", f"/api/engagements/{eid}/mappings/propose-batch",
        token=token, headers=as_pat, body={"items": "nope"})
    assert status == 400
    status, body = _request(
        port, "POST", f"/api/engagements/{eid}/mappings/approve-batch",
        token=token, headers=as_rae, body={"spec_ids": "nope"})
    assert status == 400


def test_integrity_refusal_is_named_at_the_boundary(api, tmp_path):
    """Review F3: digest tampering surfaces as a 409 naming the evidence
    chain, never an opaque 500."""
    import sqlite3
    port, auth = api
    token = auth.token
    _, created = _request(
        port, "POST", "/api/engagements", token=token,
        body={"client_name": "Acme", "period_end": "2025-12-31"})
    eid = created["engagement_id"]
    for principal, role in (("pat-preparer", "preparer"),
                            ("rae-reviewer", "reviewer")):
        _request(port, "POST", f"/api/engagements/{eid}/team", token=token,
                 body={"principal_id": principal, "role": role})
    as_pat = {"X-Acting-Principal": "pat-preparer"}
    _, artifact = _request(
        port, "POST", f"/api/engagements/{eid}/sources", token=token,
        raw_body=PAYMENTS_CSV,
        headers={**as_pat, "Content-Type": "text/csv",
                 "X-Original-Name": "payments.csv"})
    _, proposal = _request(
        port, "POST", f"/api/engagements/{eid}/mappings", token=token,
        headers=as_pat,
        body={"role": "Payments", "artifact_id": artifact["artifact_id"]})
    _request(port, "POST",
             f"/api/engagements/{eid}/mappings/{proposal['spec_id']}/approve",
             token=token, headers={"X-Acting-Principal": "rae-reviewer"},
             body={})
    status, _ = _request(
        port, "POST",
        f"/api/engagements/{eid}/mappings/{proposal['spec_id']}/normalize",
        token=token, headers=as_pat, body={})
    assert status == 200

    # Tamper behind the API's back through a second connection to the
    # same database file — the read path must refuse, by name.
    saboteur = sqlite3.connect(tmp_path / "control.db")
    saboteur.execute("UPDATE normalized_dataset SET output_digest = 'x'")
    saboteur.commit()
    saboteur.close()

    status, body = _request(port, "GET",
                            f"/api/engagements/{eid}/coverage", token=token)
    assert status == 409
    assert "recorded digest" in body["error"]


def test_manual_is_served_authenticated_and_traversal_safe(api):
    port, auth = api
    status, _ = _request(port, "GET", "/api/manual")
    assert status == 401                    # reads included, manual included
    status, listing = _request(port, "GET", "/api/manual", token=auth.token)
    assert status == 200
    names = [c["name"] for c in listing["chapters"]]
    assert names[0] == "README.md" and len(names) >= 9
    status, chapter = _request(
        port, "GET", "/api/manual/01-engagement-and-team.md",
        token=auth.token)
    assert status == 200
    assert "<h1>" in chapter["html"]
    status, _ = _request(port, "GET", "/api/manual/..%2F..%2FLICENSE.md",
                         token=auth.token)
    assert status == 404


def test_unread_bodies_do_not_poison_keepalive_connections(api):
    """A browser reuses connections. A route that replies without reading
    its JSON body (approve, normalize, export) must not leave those bytes
    in the stream, or the next request parses as garbage — observed live
    as 501 "Unsupported method ('{}GET')" while filming the demo."""
    port, auth = api
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {"Authorization": f"Bearer {auth.token}",
               "Content-Type": "application/json"}
    # A body-carrying POST to a route that raises before reading it (the
    # spec does not exist -> 404), then a GET on the SAME connection.
    conn.request("POST", "/api/engagements/nope/mappings/nope/approve",
                 body=b"{}", headers=headers)
    first = conn.getresponse()
    first.read()
    assert first.status in (404, 409)
    conn.request("GET", "/api/engagements",
                 headers={"Authorization": f"Bearer {auth.token}"})
    second = conn.getresponse()
    body = second.read()
    assert second.status == 200, body
    conn.close()
