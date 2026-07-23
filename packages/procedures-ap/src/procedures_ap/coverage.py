"""Coverage compilation: which procedures can the supplied data honestly support?

Faithful port of the prototype's compiler, output-compatible with the Phase 0
golden bundles, with one deliberate divergence (D1, see
docs/architecture/PHASE2_DIVERGENCES.md): compiling coverage never marks a
procedure ``completed``. Presence of required fields means *executable*;
completion belongs to the run lifecycle alone.
"""

from __future__ import annotations

import hashlib
import json

from procedures_ap.contracts import PROCEDURES, SCHEMA_VERSION, ProcedureContract


def _request_id(kind: str, value: str) -> str:
    raw = f"{kind}|{value}".encode("utf-8")
    return "request|" + hashlib.sha256(raw).hexdigest()[:20]


def compile_coverage(inventory: dict, *, policies: dict | None = None,
                     contracts: tuple[ProcedureContract, ...] = PROCEDURES) -> dict:
    """Compile one engagement inventory against the versioned contracts."""
    policies = policies or {}
    rows = []
    for contract in contracts:
        missing_roles = [role for role in contract.required_fields
                         if role not in inventory]
        missing_fields: dict[str, list[str]] = {}
        for role, required in contract.required_fields.items():
            if role in missing_roles:
                continue
            have = set(inventory.get(role, {}).get("fields", []))
            absent = [f for f in required if f not in have]
            if absent:
                missing_fields[role] = absent
        missing_policies = [name for name in contract.required_policies
                            if policies.get(name) in (None, "")]
        if missing_roles:
            status = "blocked"
        elif missing_fields or missing_policies:
            status = "partial"
        else:
            status = "executable"
        row = contract.to_dict()
        row.update({
            "status": status,
            "selected": contract.default_selected,
            "missing_roles": missing_roles,
            "missing_fields": missing_fields,
            "missing_policies": missing_policies,
            "population": inventory.get(contract.denominator_role, {}).get("rows"),
            # D1: never "completed" at compile time.
            "execution_status": "not_run",
        })
        rows.append(row)
    return {
        "schema_version": SCHEMA_VERSION,
        "inventory": inventory,
        "procedures": rows,
        "summary": _summary(rows),
        "evidence_requests": evidence_requests(rows),
    }


def apply_selections(coverage: dict, selections: dict) -> dict:
    """Overlay auditor selection/rationale without mutating compiled coverage."""
    result = json.loads(json.dumps(coverage))
    for row in result.get("procedures", []):
        decision = selections.get(row["procedure_id"], {})
        row["selected"] = bool(decision.get("selected", row.get("selected", True)))
        row["selection_rationale"] = str(decision.get("rationale", ""))
        row["effective_status"] = row["status"] if row["selected"] else "not_selected"
    result["summary"] = _summary(result.get("procedures", []), effective=True)
    result["evidence_requests"] = evidence_requests(result.get("procedures", []))
    return result


def apply_evidence_lifecycle(coverage: dict, records: dict) -> dict:
    """Overlay request state; compile reviewed evidence into procedure support.

    Evidence changes coverage only after a preparer validates it and a
    different reviewer approves that validation. A procedure newly supported
    this way is ``ready_to_run``: receiving a file is not execution.
    """
    result = json.loads(json.dumps(coverage))
    requests = result.get("evidence_requests", [])
    fulfilled: dict[str, dict] = {}
    for request in requests:
        current = records.get(request["request_id"], {})
        request["current"] = current
        request["status"] = current.get("status", "open")
        request["review_status"] = current.get("review_status", "not_reviewed")
        request["evidence"] = current.get("evidence", [])
        request["fulfilled"] = (
            request["status"] == "validated"
            and request["review_status"] == "approved"
        )
        if request["fulfilled"]:
            fulfilled[request["request_id"]] = request

    for procedure in result.get("procedures", []):
        original_status = procedure.get("status", "blocked")
        support = [request for request in fulfilled.values()
                   if procedure.get("procedure_id") in request.get("unlocks", [])]
        for request in support:
            if request["kind"] == "dataset":
                procedure["missing_roles"] = [
                    role for role in procedure.get("missing_roles", [])
                    if role != request["item"]
                ]
            elif request["kind"] == "field" and "." in request["item"]:
                role, fieldname = request["item"].split(".", 1)
                fields = [name for name in
                          procedure.get("missing_fields", {}).get(role, [])
                          if name != fieldname]
                if fields:
                    procedure.setdefault("missing_fields", {})[role] = fields
                else:
                    procedure.get("missing_fields", {}).pop(role, None)
            elif request["kind"] == "policy":
                procedure["missing_policies"] = [
                    policy for policy in procedure.get("missing_policies", [])
                    if policy != request["item"]
                ]
        if procedure.get("missing_roles"):
            status = "blocked"
        elif procedure.get("missing_fields") or procedure.get("missing_policies"):
            status = "partial"
        else:
            status = "executable"
        procedure["status"] = status
        procedure["effective_status"] = (
            status if procedure.get("selected", True) else "not_selected"
        )
        procedure["supporting_evidence"] = [
            {"request_id": request["request_id"], "item": request["item"],
             "evidence": request.get("evidence", [])}
            for request in support
        ]
        if original_status != "executable" and status == "executable":
            procedure["execution_status"] = "ready_to_run"

    result["summary"] = _summary(result.get("procedures", []), effective=True)
    result["request_summary"] = {
        status: sum(1 for request in requests if request.get("status") == status)
        for status in ("open", "requested", "received", "validated",
                       "rejected", "superseded")
    }
    result["open_evidence_requests"] = [
        request for request in requests if not request.get("fulfilled")
        and request.get("status") != "superseded"
    ]
    return result


def _summary(rows: list[dict], effective: bool = False) -> dict:
    counts = {name: 0 for name in ("executable", "partial", "blocked", "not_selected")}
    for row in rows:
        status = row.get("effective_status") if effective else row.get("status")
        counts[status] = counts.get(status, 0) + 1
    return {**counts, "total": len(rows)}


def evidence_requests(rows: list[dict]) -> list[dict]:
    """Group missing roles/fields/policies into requests tied to procedures."""
    grouped: dict[tuple[str, str], dict] = {}
    for row in rows:
        if not row.get("selected", True):
            continue
        for role in row.get("missing_roles", []):
            key = ("role", role)
            request = grouped.setdefault(key, {
                "request_id": _request_id(*key), "kind": "dataset",
                "item": role, "owner": "client data owner", "unlocks": [],
                "cycles": set(), "assertions": set(),
            })
            request["unlocks"].append(row["procedure_id"])
            request["cycles"].add(row["cycle"])
            request["assertions"].update(row["assertions"])
        for role, fields in row.get("missing_fields", {}).items():
            for fieldname in fields:
                key = ("field", f"{role}.{fieldname}")
                request = grouped.setdefault(key, {
                    "request_id": _request_id(*key), "kind": "field",
                    "item": f"{role}.{fieldname}", "owner": "client data owner",
                    "unlocks": [], "cycles": set(), "assertions": set(),
                })
                request["unlocks"].append(row["procedure_id"])
                request["cycles"].add(row["cycle"])
                request["assertions"].update(row["assertions"])
        for policy in row.get("missing_policies", []):
            key = ("policy", policy)
            request = grouped.setdefault(key, {
                "request_id": _request_id(*key), "kind": "policy",
                "item": policy, "owner": "engagement team", "unlocks": [],
                "cycles": set(), "assertions": set(),
            })
            request["unlocks"].append(row["procedure_id"])
            request["cycles"].add(row["cycle"])
            request["assertions"].update(row["assertions"])
    out = []
    for request in grouped.values():
        request["unlocks"] = sorted(set(request["unlocks"]))
        request["cycles"] = sorted(request["cycles"])
        request["assertions"] = sorted(request["assertions"])
        out.append(request)
    return sorted(out, key=lambda item: (item["kind"], item["item"]))
