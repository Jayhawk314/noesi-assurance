"""Run the local workbench: API + built review UI on loopback.

    python -m workbench_api [--data DIR] [--port N]

Prints the one-session bearer token; paste it into the UI's token gate.
"""

from __future__ import annotations

import argparse
import getpass
from pathlib import Path

from assurance_application.service import WorkbenchService
from assurance_artifacts.signing import LocalKeyStore
from assurance_artifacts.vault import ArtifactVault
from assurance_persistence.database import connect, migrate
from assurance_persistence.legacy_import import ensure_tenant

from workbench_api.server import SessionAuth, build_server

_UI_DIST = Path(__file__).resolve().parents[2] / "workbench-ui" / "dist"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=str(Path.home() / ".noesi-assurance"),
                        help="data directory (control DB, vault, keys)")
    parser.add_argument("--port", type=int, default=8347)
    parser.add_argument("--principal", default=f"local:{getpass.getuser()}",
                        help="principal id for this session")
    parser.add_argument("--demo", nargs="?", const="", default=None,
                        metavar="CASE_DIR",
                        help="seed the Harborline demo engagement (optionally "
                             "from an explicit case data directory)")
    args = parser.parse_args(argv)

    data = Path(args.data)
    data.mkdir(parents=True, exist_ok=True)
    conn = connect(data / "control.db", allow_cross_thread=True)
    migrate(conn)
    tenant = ensure_tenant(conn, "local")
    service = WorkbenchService(
        conn, ArtifactVault(data / "vault"), tenant,
        keystore=LocalKeyStore(data / "keys"))
    auth = SessionAuth.create(args.principal)
    static = _UI_DIST if _UI_DIST.is_dir() else None
    server = build_server(service, auth, port=args.port, static_dir=static)

    demo_note = ""
    if args.demo is not None:
        from workbench_api.demo import seed_demo
        outcome = seed_demo(service, args.principal,
                            case_dir=Path(args.demo) if args.demo else None)
        demo_note = ("seeded — switch chairs in the UI to run procedures"
                     if outcome["seeded"] else "already present")

    port = server.server_address[1]
    # flush=True: the token must reach a redirected log immediately.
    print(f"workbench:  http://127.0.0.1:{port}/"
          + ("" if static else "   (UI not built; API only)"), flush=True)
    print(f"principal:  {args.principal}", flush=True)
    print(f"token:      {auth.token}", flush=True)
    if demo_note:
        print(f"demo:       Harborline Marine Group ({demo_note})", flush=True)
    print("Ctrl+C stops the server. The token dies with it.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
