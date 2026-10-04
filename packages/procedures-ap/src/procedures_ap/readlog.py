# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Which tables and policies a procedure run actually read.

A run's result depends only on what its engine read. Recording that lets the
Workbench say a result is stale when one of *those* inputs changed, and not
when an unrelated file or setting changed (3 Oct 2026: every result was
marked stale after any upload or setting change).

Tables are logged where every engine opens one (the ``records`` helpers),
so a copied table mapping or a role that is absent is still recorded: a
procedure that looked for payments and found none depends on payments
arriving later. Policies are logged by the mapping handed to the engine;
any whole-mapping access (iteration, keys, items) marks every policy read.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

_ROLES: ContextVar[set | None] = ContextVar("noesi_roles_read", default=None)


def note_role(role: str) -> None:
    """Record that the running procedure looked up table ``role``."""
    log = _ROLES.get()
    if log is not None:
        log.add(role)


class TrackedPolicies(dict):
    """A policies mapping that records which names were consulted."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read: set[str] = set()
        self.read_all = False

    def __getitem__(self, key):
        self.read.add(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        self.read.add(key)
        return super().get(key, default)

    def __contains__(self, key):
        self.read.add(key)
        return super().__contains__(key)

    def _everything(self):
        self.read_all = True

    def keys(self):
        self._everything()
        return super().keys()

    def items(self):
        self._everything()
        return super().items()

    def values(self):
        self._everything()
        return super().values()

    def __iter__(self):
        self._everything()
        return super().__iter__()

    def copy(self):
        self._everything()
        return dict(super().items())


@contextmanager
def reading():
    """Collect the roles read inside the block: ``with reading() as roles:``."""
    roles: set = set()
    token = _ROLES.set(roles)
    try:
        yield roles
    finally:
        _ROLES.reset(token)
