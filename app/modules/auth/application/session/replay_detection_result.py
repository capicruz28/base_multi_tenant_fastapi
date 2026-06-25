"""Resultado de detección y cierre por replay attack (RTR V2)."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ReplayDetectionResult:
    """Post handle_replay_attack_tx — familia comprometida y sesión cerrada."""

    session_id: UUID
    family_id: UUID
    token_id: UUID
    cliente_id: UUID
    usuario_id: UUID


__all__ = ["ReplayDetectionResult"]
