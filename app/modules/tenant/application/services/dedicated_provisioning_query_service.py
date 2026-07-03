"""
Servicio de consulta read-only — provisioning Dedicated (PR-F4-02).

Compone snapshot CP sin mutaciones. Base para F4-11 status API.
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.repositories.tenant_provisioning_repository import (
    TenantProvisioningRepository,
)
from app.modules.tenant.application.provisioning import (
    DEDICATED_INSTALLATION_TYPE,
    ProvisioningState,
)
from app.modules.tenant.application.provisioning.provisioning_status_read import (
    DedicatedProvisioningStatusSnapshot,
    ProvisioningStepStatusRead,
)

logger = logging.getLogger(__name__)


class DedicatedProvisioningQueryService:
    """Queries internas de estado provisioning — read-only."""

    def __init__(
        self,
        repository: Optional[TenantProvisioningRepository] = None,
    ) -> None:
        self._repo = repository or TenantProvisioningRepository()

    async def get_provisioning_status(
        self,
        cliente_id: UUID,
    ) -> Optional[DedicatedProvisioningStatusSnapshot]:
        """
        Devuelve snapshot interno alineado al contrato §9.

        ``None`` si el cliente no existe. Legacy dedicated sin estado → snapshot
        con ``provisioning_state=None`` (decisión §18 contrato).
        """
        snapshot = await self._repo.get_cliente_provisioning_snapshot(cliente_id)
        if not snapshot:
            return None

        run_id = snapshot.get("current_provisioning_run_id")
        run_row = None
        steps_rows: list[dict] = []

        if run_id:
            run_row = await self._repo.get_run_by_id(run_id, cliente_id)
            if run_row:
                steps_rows = await self._repo.list_steps_for_run(run_id, cliente_id)

        return _build_status_snapshot(
            cliente_snapshot=snapshot,
            run_row=run_row,
            steps_rows=steps_rows,
        )

    async def get_provisioning_status_or_raise(
        self,
        cliente_id: UUID,
    ) -> DedicatedProvisioningStatusSnapshot:
        status = await self.get_provisioning_status(cliente_id)
        if status is None:
            raise NotFoundError(
                detail=f"Cliente {cliente_id} no encontrado.",
                internal_code="CLIENTE_NOT_FOUND",
            )
        return status

    async def has_active_provisioning(self, cliente_id: UUID) -> bool:
        run = await self._repo.get_current_run(cliente_id)
        if not run:
            return False
        return run.get("provisioning_state") == ProvisioningState.PROVISIONING.value

    async def is_dedicated_with_provisioning_state(
        self,
        cliente_id: UUID,
    ) -> bool:
        snapshot = await self._repo.get_cliente_provisioning_snapshot(cliente_id)
        if not snapshot:
            return False
        return (
            snapshot.get("tipo_instalacion") == DEDICATED_INSTALLATION_TYPE
            and snapshot.get("provisioning_state") is not None
        )


def _build_status_snapshot(
    *,
    cliente_snapshot: dict,
    run_row: Optional[dict],
    steps_rows: list[dict],
) -> DedicatedProvisioningStatusSnapshot:
    raw_state = cliente_snapshot.get("provisioning_state")
    state = ProvisioningState(raw_state) if raw_state else None

    steps = [
        ProvisioningStepStatusRead(
            code=row["step_code"],
            status=row["step_status"],
            started_at=row.get("started_at"),
            completed_at=row.get("completed_at"),
        )
        for row in steps_rows
    ]

    retry_allowed = state == ProvisioningState.FAILED
    abort_allowed = state == ProvisioningState.PROVISIONING

    return DedicatedProvisioningStatusSnapshot(
        cliente_id=cliente_snapshot["cliente_id"],
        tipo_instalacion=cliente_snapshot["tipo_instalacion"],
        provisioning_state=state,
        provisioning_run_id=(
            run_row["provisioning_run_id"] if run_row else cliente_snapshot.get("current_provisioning_run_id")
        ),
        current_step=run_row.get("current_step_code") if run_row else None,
        steps=steps,
        started_at=run_row.get("started_at") if run_row else None,
        updated_at=run_row.get("updated_at") if run_row else None,
        ready_at=run_row.get("ready_at") if run_row else None,
        failed_at=run_row.get("failed_at") if run_row else None,
        last_error_code=run_row.get("last_error_code") if run_row else None,
        last_error_message=run_row.get("last_error_message") if run_row else None,
        retry_allowed=retry_allowed,
        abort_allowed=abort_allowed,
    )


__all__ = ["DedicatedProvisioningQueryService"]
