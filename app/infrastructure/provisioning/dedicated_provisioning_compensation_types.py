"""Contratos internos — DedicatedProvisioningCompensationService (PR-F4-10)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ProvisioningCompensationResult:
    """Resultado compensación semi-automática S10→S3."""

    cliente_id: UUID
    provisioning_run_id: UUID
    steps_compensated: tuple[str, ...]
    database_dropped: bool
    connection_deactivated: bool
    cache_invalidated: bool
    steps_reset_from_order: Optional[int]
    idempotent: bool = False


@dataclass(frozen=True, slots=True)
class ProvisioningAbortResult:
    """Resultado abort interno — failed + compensación."""

    cliente_id: UUID
    provisioning_run_id: UUID
    compensation: ProvisioningCompensationResult


__all__ = [
    "ProvisioningAbortResult",
    "ProvisioningCompensationResult",
]
