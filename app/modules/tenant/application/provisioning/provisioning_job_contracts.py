"""Contratos internos — job dispatcher provisioning (PR-F4-03 / F4-08)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable, Optional, Protocol
from uuid import UUID

from app.modules.tenant.application.provisioning.provisioning_saga_ephemeral_context import (
    ProvisioningSagaEphemeralContext,
)


class ProvisioningJobHandler(Protocol):
    """Handler in-process; saga orchestrator F4-08 implementa este contrato."""

    async def __call__(self, job: "ProvisioningJobRequest") -> None: ...


ProvisioningJobHandlerCallable = Callable[["ProvisioningJobRequest"], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class ProvisioningJobRequest:
    """Payload mínimo para despacho — correlación ``cliente_id`` + ``run_id``."""

    cliente_id: UUID
    provisioning_run_id: UUID
    idempotency_key: Optional[str] = None
    enqueued_at: Optional[datetime] = None
    trigger_source: str = "internal"
    ephemeral_context: Optional[ProvisioningSagaEphemeralContext] = None

@dataclass(frozen=True, slots=True)
class ProvisioningJobDispatchResult:
    """Resultado síncrono del despacho (no implica saga completada)."""

    cliente_id: UUID
    provisioning_run_id: UUID
    dispatched: bool
    sync_execution: bool
    dispatcher_enabled: bool
    enqueued_at: datetime


__all__ = [
    "ProvisioningJobDispatchResult",
    "ProvisioningJobHandler",
    "ProvisioningJobHandlerCallable",
    "ProvisioningJobRequest",
]
