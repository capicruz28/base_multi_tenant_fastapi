"""Contratos internos — DedicatedActivationService (PR-F4-08 / F4-09)."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DedicatedActivationRequest:
    cliente_id: UUID
    provisioning_run_id: UUID
    database_name: str
    servidor: str
    app_login_name: str
    app_login_password: str


@dataclass(frozen=True, slots=True)
class DedicatedActivationStepResult:
    step_code: str
    idempotency_marker: str
    stub: bool = False
    idempotent: bool = False


__all__ = ["DedicatedActivationRequest", "DedicatedActivationStepResult"]
