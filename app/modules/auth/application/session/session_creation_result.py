"""Resultado de creación de sesión V3 (login / password change)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class SessionCreationResult:
    """IDs y TTL absoluto tras create_session_with_token_tx."""

    session_id: UUID
    family_id: UUID
    token_id: UUID
    expires_at: datetime


__all__ = ["SessionCreationResult"]
