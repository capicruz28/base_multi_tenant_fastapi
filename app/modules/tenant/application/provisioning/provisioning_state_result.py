"""DTOs internos — resultados mutación provisioning (PR-F4-02)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.modules.tenant.application.provisioning.provisioning_state import (
    ProvisioningState,
)
from app.modules.tenant.application.provisioning.provisioning_step_code import (
    ProvisioningStepCode,
)


@dataclass(frozen=True, slots=True)
class ProvisioningRunInitializedResult:
    provisioning_run_id: UUID
    cliente_id: UUID
    provisioning_state: ProvisioningState
    attempt_number: int
    idempotency_key: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ProvisioningStateTransitionResult:
    provisioning_run_id: UUID
    cliente_id: UUID
    previous_state: ProvisioningState
    current_state: ProvisioningState
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ProvisioningStepTransitionResult:
    provisioning_run_id: UUID
    cliente_id: UUID
    step_code: ProvisioningStepCode
    previous_status: str
    current_status: str
    updated_at: datetime


__all__ = [
    "ProvisioningRunInitializedResult",
    "ProvisioningStateTransitionResult",
    "ProvisioningStepTransitionResult",
]
