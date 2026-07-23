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
    server = build_server(service, auth, port=0)
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

    # The single session principal cannot approve their own mapping — the
    # server enforces it; this is the pilot's honest single-user limit.
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
