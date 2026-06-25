"""Resultado de revocación de sesión (logout / self-revoke / admin)."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RevokeResult:
    """Idempotente: already_revoked=True si la sesión ya estaba cerrada."""

    session_id: UUID
    was_active: bool
    already_revoked: bool = False


__all__ = ["RevokeResult"]
