"""Resultado canónico de rotación atómica de refresh tokens (IAM P1-04)."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, Optional
from uuid import UUID


class RotateOutcome(StrEnum):
    """Estado terminal de una rotación atómica."""

    ROTATED = "rotated"
    IDLE_TIMEOUT = "idle_timeout"
    NOT_FOUND = "not_found"
    EXPIRED = "expired"
    ALREADY_REVOKED = "already_revoked"
    ALREADY_ROTATED = "already_rotated"
    USER_MISMATCH = "user_mismatch"


@dataclass(frozen=True)
class RotateResult:
    """
    Resultado de rotate_refresh_token_service().

    Dark code P1-04: consumido por POST /auth/refresh/ (P1-04-IMPL-02).
    """

    outcome: RotateOutcome
    cliente_id: UUID
    usuario_id: Optional[UUID] = None
    old_token_id: Optional[UUID] = None
    new_token_id: Optional[UUID] = None
    revoked_reason: Optional[str] = None
    old_token_row: Optional[Dict[str, Any]] = field(default=None, compare=False)
    new_token_row: Optional[Dict[str, Any]] = field(default=None, compare=False)

    @property
    def success(self) -> bool:
        return self.outcome == RotateOutcome.ROTATED

    @property
    def idle_expired(self) -> bool:
        return self.outcome == RotateOutcome.IDLE_TIMEOUT


__all__ = ["RotateOutcome", "RotateResult"]
