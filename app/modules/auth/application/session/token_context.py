"""Agregado lectura token + familia + sesión (SessionQueryService)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import UUID


@dataclass(frozen=True)
class TokenContext:
    """Snapshot read-only de las tres entidades v3 para un token vigente o any-state."""

    cliente_id: UUID
    session_id: UUID
    family_id: UUID
    token_id: UUID
    session_row: Mapping[str, Any]
    family_row: Mapping[str, Any]
    token_row: Mapping[str, Any]


__all__ = ["TokenContext"]
