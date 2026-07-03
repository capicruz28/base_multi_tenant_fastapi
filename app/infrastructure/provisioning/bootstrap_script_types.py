"""Contratos internos — BootstrapScriptRunner (PR-F4-05)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BootstrapScriptRunRequest:
    """Entrada S4–S5 saga — bootstrap schema en BD dedicada."""

    database_name: str
    cliente_id: UUID
    provisioning_run_id: Optional[UUID] = None
    profile: str = "dedicated_schema_v2"


@dataclass(frozen=True, slots=True)
class BootstrapScriptRunResult:
    """Resultado bootstrap schema — consumo interno saga F4-08."""

    database_name: str
    cliente_id: UUID
    profile: str
    scripts_executed: tuple[str, ...]
    scripts_skipped: tuple[str, ...]
    batches_executed: int


__all__ = [
    "BootstrapScriptRunRequest",
    "BootstrapScriptRunResult",
]
