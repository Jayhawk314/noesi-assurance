"""Domain errors shared across ports and adapters."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for domain-rule violations."""


class ConflictError(DomainError):
    """Optimistic version check failed: the entity changed under the caller."""

    def __init__(self, entity_type: str, entity_id: str, expected_version: int):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.expected_version = expected_version
        super().__init__(
            f"{entity_type} {entity_id} is no longer at version {expected_version}"
        )


class NotFoundError(DomainError):
    """The referenced entity does not exist in the caller's engagement scope."""
