"""Explicit state machines for procedure runs and evidence.

The prototype had two run models (base procedures "completed" by inference,
incremental ones with receipts). Here every procedure run walks one
lifecycle, and presence of required fields means *executable*, never
completed. Evidence changes coverage only after preparer validation and a
different reviewer's approval; that separation is enforced here, not in a UI.
"""

from __future__ import annotations


class InvalidTransition(ValueError):
    def __init__(self, kind: str, current: str, target: str):
        self.kind, self.current, self.target = kind, current, target
        super().__init__(f"{kind}: illegal transition {current!r} -> {target!r}")


class SeparationOfDutiesError(ValueError):
    """The same principal may not both prepare and approve."""


PROCEDURE_RUN_STATES = (
    "planned", "executable", "queued", "running",
    "completed", "error", "reviewed", "approved",
)

PROCEDURE_RUN_TRANSITIONS: dict[str, frozenset[str]] = {
    "planned": frozenset({"executable"}),
    "executable": frozenset({"queued", "planned"}),   # planning can regress
    "queued": frozenset({"running"}),
    "running": frozenset({"completed", "error"}),
    "completed": frozenset({"reviewed"}),
    "error": frozenset({"queued"}),                   # rerun after correction
    "reviewed": frozenset({"approved", "queued"}),    # reviewer may send back
    "approved": frozenset(),                          # terminal
}

EVIDENCE_STATES = (
    "open", "requested", "received", "validated", "rejected", "superseded",
)

EVIDENCE_TRANSITIONS: dict[str, frozenset[str]] = {
    "open": frozenset({"requested"}),
    "requested": frozenset({"received"}),
    "received": frozenset({"validated", "rejected"}),
    "rejected": frozenset({"received"}),              # client resubmits
    "validated": frozenset({"superseded"}),
    "superseded": frozenset(),                        # terminal
}

_MACHINES = {
    "procedure_run": PROCEDURE_RUN_TRANSITIONS,
    "evidence": EVIDENCE_TRANSITIONS,
}


def advance(kind: str, current: str, target: str) -> str:
    """Validate one transition; returns the new state or raises."""
    transitions = _MACHINES.get(kind)
    if transitions is None:
        raise ValueError(f"unknown state machine {kind!r}")
    if current not in transitions:
        raise ValueError(f"{kind}: unknown state {current!r}")
    if target not in transitions[current]:
        raise InvalidTransition(kind, current, target)
    return target


def require_separation(*, prepared_by: str, approved_by: str) -> None:
    """Preparer and approver must be different authenticated principals."""
    if not prepared_by.strip() or not approved_by.strip():
        raise SeparationOfDutiesError("both principals must be identified")
    if prepared_by == approved_by:
        raise SeparationOfDutiesError(
            "the preparing principal may not approve their own work")
