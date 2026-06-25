"""Contexto read-only de sesión para GET /me/ (SessionProbeService)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class SessionProbeResult:
    """Fail-soft: campos opcionales cuando no hay refresh ni claim sid."""

    current_session_id: Optional[UUID] = None
    current_token_id: Optional[UUID] = None
    is_active: bool = False


__all__ = ["SessionProbeResult"]
