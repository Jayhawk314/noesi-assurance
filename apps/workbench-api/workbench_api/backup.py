# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Create, verify, or restore a Noesi Workbench backup.

Restore is deliberately offline: restore into a new data directory, then
start the Workbench with ``--data`` pointing at it.

    python -m workbench_api.backup create --data DIR --to FILE
    python -m workbench_api.backup verify FILE
    python -m workbench_api.backup restore FILE --data NEW_DIR
"""

from __future__ import annotations

import argparse
import json
import sys

from assurance_application.backup import (
    BackupRefused,
    create_backup,
    restore_backup,
    verify_backup,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="back up a Workbench data directory")
    create.add_argument("--data", required=True, help="source data directory")
    create.add_argument("--to", required=True, help="new backup zip file")

    verify = commands.add_parser("verify", help="check a backup without restoring it")
    verify.add_argument("backup", help="backup zip file to check")

    restore = commands.add_parser("restore", help="restore into a new, offline data directory")
    restore.add_argument("backup", help="backup zip file to restore")
    restore.add_argument("--data", required=True,
                         help="new or empty destination data directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "create":
            report = create_backup(args.data, args.to)
        elif args.command == "verify":
            report = verify_backup(args.backup)
        else:
            report = restore_backup(args.backup, args.data)
    except BackupRefused as exc:
        print("backup operation refused:", file=sys.stderr)
        for problem in exc.problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"backup operation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
