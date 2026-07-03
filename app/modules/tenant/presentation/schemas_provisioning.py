"""Schemas públicos — Dedicated Provisioning Operations API (PR-F4-11)."""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.tenant.application.provisioning import DEDICATED_INSTALLATION_TYPE, ProvisioningState
from app.modules.tenant.application.provisioning.provisioning_status_read import (
    DedicatedProvisioningStatusSnapshot,
)

_SENSITIVE_ERROR_RE = re.compile(
    r"(password|passwd|pwd|secret|connection\s*string|usuario\s*=|login\s*=|"
    r"nvarchar|varchar|sql\s*server|traceback)",
    re.IGNORECASE,
)


class ProvisioningStepPublicRead(BaseModel):
  code: str = Field(..., description="Código step saga §9.1 contrato.")
  status: str = Field(..., description="pending|running|completed|failed|skipped")
  started_at: Optional[datetime] = None
  completed_at: Optional[datetime] = None

  class Config:
    from_attributes = True


class DedicatedProvisioningStatusRead(BaseModel):
  cliente_id: UUID
  provisioning_state: Optional[str] = Field(
      None,
      description="provisioning|ready|failed",
  )
  provisioning_run_id: Optional[UUID] = None
  current_step: Optional[str] = None
  steps: List[ProvisioningStepPublicRead] = Field(default_factory=list)
  started_at: Optional[datetime] = None
  updated_at: Optional[datetime] = None
  ready_at: Optional[datetime] = None
  failed_at: Optional[datetime] = None
  last_error_code: Optional[str] = None
  last_error_message: Optional[str] = None
  retry_allowed: bool = False
  abort_allowed: bool = False

  class Config:
    from_attributes = True


class ProvisioningRetryResponse(BaseModel):
  success: bool = True
  message: str
  provisioning_run_id: UUID
  provisioning_state: str = "provisioning"

  class Config:
    from_attributes = True


class ProvisioningAbortRequest(BaseModel):
  reason: Optional[str] = Field(
      None,
      max_length=500,
      description="Motivo ops-safe del abort.",
  )


class ProvisioningAbortResponse(BaseModel):
  success: bool = True
  message: str
  provisioning_state: str = "failed"
  cleanup_checklist_url: Optional[str] = None

  class Config:
    from_attributes = True


def sanitize_provisioning_error_message(message: Optional[str]) -> Optional[str]:
  if not message:
    return None
  trimmed = message.strip()
  if not trimmed:
    return None
  if _SENSITIVE_ERROR_RE.search(trimmed):
    return "Error de provisioning. Consulte soporte con el código de error."
  return trimmed[:500]


def build_legacy_ready_status_read(cliente_id: UUID) -> DedicatedProvisioningStatusRead:
  """Dedicated legacy sin ``provisioning_state`` — respuesta sintética §18."""
  return DedicatedProvisioningStatusRead(
      cliente_id=cliente_id,
      provisioning_state=ProvisioningState.READY.value,
      provisioning_run_id=None,
      current_step=None,
      steps=[],
      started_at=None,
      updated_at=None,
      ready_at=None,
      failed_at=None,
      last_error_code=None,
      last_error_message=None,
      retry_allowed=False,
      abort_allowed=False,
  )


def map_provisioning_status_to_read(
    snapshot: DedicatedProvisioningStatusSnapshot,
) -> DedicatedProvisioningStatusRead:
  state_value = (
      snapshot.provisioning_state.value
      if snapshot.provisioning_state is not None
      else None
  )
  return DedicatedProvisioningStatusRead(
      cliente_id=snapshot.cliente_id,
      provisioning_state=state_value,
      provisioning_run_id=snapshot.provisioning_run_id,
      current_step=snapshot.current_step,
      steps=[
          ProvisioningStepPublicRead(
              code=step.code,
              status=step.status,
              started_at=step.started_at,
              completed_at=step.completed_at,
          )
          for step in snapshot.steps
      ],
      started_at=snapshot.started_at,
      updated_at=snapshot.updated_at,
      ready_at=snapshot.ready_at,
      failed_at=snapshot.failed_at,
      last_error_code=snapshot.last_error_code,
      last_error_message=sanitize_provisioning_error_message(
          snapshot.last_error_message,
      ),
      retry_allowed=snapshot.retry_allowed,
      abort_allowed=snapshot.abort_allowed,
  )


def is_dedicated_tenant(snapshot: DedicatedProvisioningStatusSnapshot) -> bool:
  return snapshot.tipo_instalacion == DEDICATED_INSTALLATION_TYPE


def is_legacy_dedicated_without_provisioning(
    snapshot: DedicatedProvisioningStatusSnapshot,
) -> bool:
  return (
      snapshot.tipo_instalacion == DEDICATED_INSTALLATION_TYPE
      and snapshot.provisioning_state is None
  )


__all__ = [
    "DedicatedProvisioningStatusRead",
    "ProvisioningAbortRequest",
    "ProvisioningAbortResponse",
    "ProvisioningRetryResponse",
    "ProvisioningStepPublicRead",
    "build_legacy_ready_status_read",
    "is_dedicated_tenant",
    "is_legacy_dedicated_without_provisioning",
    "map_provisioning_status_to_read",
    "sanitize_provisioning_error_message",
]
