"""DTO read-only — status provisioning interno (PR-F4-02)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.modules.tenant.application.provisioning.provisioning_state import (
    ProvisioningState,
)


@dataclass(frozen=True, slots=True)
class ProvisioningStepStatusRead:
    code: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


@dataclass(frozen=True, slots=True)
class DedicatedProvisioningStatusSnapshot:
    """Shape interno alineado a DEDICATED_PROVISIONING_API_CONTRACT §9."""

    cliente_id: UUID
    tipo_instalacion: str
    provisioning_state: Optional[ProvisioningState]
    provisioning_run_id: Optional[UUID]
    current_step: Optional[str]
    steps: List[ProvisioningStepStatusRead]
    started_at: Optional[datetime]
    updated_at: Optional[datetime]
    ready_at: Optional[datetime]
    failed_at: Optional[datetime]
    last_error_code: Optional[str]
    last_error_message: Optional[str]
    retry_allowed: bool
    abort_allowed: bool


__all__ = [
    "DedicatedProvisioningStatusSnapshot",
    "ProvisioningStepStatusRead",
]
