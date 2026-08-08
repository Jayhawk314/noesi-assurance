# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""The stable worker protocol: frozen job manifests and result bundles.

A procedure never runs against "whatever is loaded" — it runs against a
manifest that freezes the procedure version, engine version, input table
digests, policies, and parameters. ``run_job`` refuses inputs whose digests
do not match the manifest. Workers stay deterministic functions; the
coordinator owns workflow, so a result bundle carries no workflow mutations.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Callable

PROTOCOL_VERSION = "noesi-worker-protocol-v1"


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str)


def table_digest(records: list[dict]) -> str:
    return hashlib.sha256(_canonical(records).encode("utf-8")).hexdigest()


class InputMismatchError(ValueError):
    """Supplied inputs do not match the frozen job manifest."""


@dataclass(frozen=True)
class JobManifest:
    procedure_id: str
    procedure_version: str
    engine_version: str
    input_tables: dict  # role -> {"rows": int, "sha256": str}
    policies: dict = field(default_factory=dict)
    parameters: dict = field(default_factory=dict)
    rerun_sequence: int = 0

    @property
    def job_id(self) -> str:
        payload = _canonical({
            "protocol": PROTOCOL_VERSION,
            "procedure_id": self.procedure_id,
            "procedure_version": self.procedure_version,
            "engine_version": self.engine_version,
            "input_tables": self.input_tables,
            "policies": self.policies,
            "parameters": self.parameters,
            "rerun_sequence": self.rerun_sequence,
        })
        return "job|" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ResultBundle:
    job_id: str
    status: str  # "completed" | "error"
    summary: dict
    findings: tuple[dict, ...]  # receipt dicts, content-addressed
    error: str = ""

    @property
    def result_digest(self) -> str:
        payload = _canonical({
            "job_id": self.job_id, "status": self.status,
            "summary": self.summary, "findings": list(self.findings),
            "error": self.error,
        })
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id, "status": self.status,
            "summary": self.summary, "findings": list(self.findings),
            "error": self.error, "result_digest": self.result_digest,
        }


def build_manifest(*, procedure_id: str, procedure_version: str,
                   engine_version: str, tables: dict,
                   policies: dict | None = None,
                   parameters: dict | None = None,
                   rerun_sequence: int = 0) -> JobManifest:
    return JobManifest(
        procedure_id=procedure_id, procedure_version=procedure_version,
        engine_version=engine_version,
        input_tables={
            role: {"rows": len(records), "sha256": table_digest(records)}
            for role, records in sorted(tables.items())},
        policies=dict(policies or {}), parameters=dict(parameters or {}),
        rerun_sequence=rerun_sequence)


def run_job(manifest: JobManifest, tables: dict,
            executor: Callable[[str, dict, dict], tuple[list, dict]],
            ) -> ResultBundle:
    """Execute one job against verified inputs; never raises executor errors."""
    for role, declared in manifest.input_tables.items():
        supplied = tables.get(role)
        if supplied is None:
            raise InputMismatchError(f"manifest table {role!r} was not supplied")
        if table_digest(list(supplied)) != declared["sha256"]:
            raise InputMismatchError(
                f"supplied table {role!r} does not match the frozen manifest")
    extra = set(tables) - set(manifest.input_tables)
    if extra:
        raise InputMismatchError(
            f"tables outside the manifest were supplied: {sorted(extra)}")
    try:
        findings, summary = executor(
            manifest.procedure_id, tables, manifest.policies)
        return ResultBundle(
            job_id=manifest.job_id, status="completed", summary=summary,
            findings=tuple(item.to_dict() for item in findings))
    except ValueError as exc:
        return ResultBundle(
            job_id=manifest.job_id, status="error",
            summary={"population": 0, "exceptions": 0},
            findings=(), error=str(exc))
