"""Modelos internos de dominio — persistencia provisioning CP."""
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
from app.modules.tenant.application.provisioning.provisioning_step_status import (
    ProvisioningStepStatus,
)


@dataclass(frozen=True, slots=True)
class TenantProvisioningRunRecord:
    provisioning_run_id: UUID
    cliente_id: UUID
    provisioning_state: ProvisioningState
    is_current: bool
    attempt_number: int
    started_at: datetime
    updated_at: datetime
    idempotency_key: Optional[str] = None
    current_step_code: Optional[ProvisioningStepCode] = None
    ready_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    last_error_code: Optional[str] = None
    last_error_message: Optional[str] = None
    created_by_usuario_id: Optional[UUID] = None


@dataclass(frozen=True, slots=True)
class TenantProvisioningStepRecord:
    provisioning_step_id: UUID
    provisioning_run_id: UUID
    cliente_id: UUID
    step_code: ProvisioningStepCode
    saga_order: int
    step_status: ProvisioningStepStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    idempotency_marker: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ClienteProvisioningSnapshot:
    cliente_id: UUID
    tipo_instalacion: str
    provisioning_state: Optional[ProvisioningState]
    current_provisioning_run_id: Optional[UUID]


__all__ = [
    "ClienteProvisioningSnapshot",
    "TenantProvisioningRunRecord",
    "TenantProvisioningStepRecord",
]
