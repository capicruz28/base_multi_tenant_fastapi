"""
Repositorio CP — state model Dedicated provisioning (PR-F4-01).

Persistencia sin orquestación saga. Consumido por PR-F4-02 state service.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries.tenant.provisioning import (
    cliente_provisioning_state_queries_core as cpsq,
    tenant_provisioning_run_queries_core as runq,
    tenant_provisioning_step_queries_core as stepq,
)
from app.infrastructure.database.queries_async import execute_insert, execute_query, execute_update
from app.infrastructure.database.repositories.base_repository import BaseRepository
from app.modules.tenant.application.provisioning import ProvisioningState

logger = logging.getLogger(__name__)


class TenantProvisioningRepository(BaseRepository):
    """Acceso a datos provisioning CP (ADMIN)."""

    def __init__(self) -> None:
        super().__init__(
            table_name="tenant_provisioning_run",
            id_column="provisioning_run_id",
            tenant_column="cliente_id",
            connection_type=DatabaseConnection.ADMIN,
        )

    @staticmethod
    def _first_row(rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        return rows[0] if rows else None

    async def get_run_by_id(
        self,
        provisioning_run_id: UUID,
        cliente_id: UUID,
        *,
        session: Optional[AsyncSession] = None,
    ) -> Optional[Dict[str, Any]]:
        stmt = runq.select_run_by_id_stmt(provisioning_run_id, cliente_id)
        if session is not None:
            result = await session.execute(stmt)
            row = result.mappings().first()
            return runq.map_run_row(dict(row)) if row else None
        rows = await execute_query(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        mapped = runq.map_run_rows(rows)
        return self._first_row(mapped)

    async def get_current_run(
        self,
        cliente_id: UUID,
        *,
        session: Optional[AsyncSession] = None,
    ) -> Optional[Dict[str, Any]]:
        stmt = runq.select_current_run_for_cliente_stmt(cliente_id)
        if session is not None:
            result = await session.execute(stmt)
            row = result.mappings().first()
            return runq.map_run_row(dict(row)) if row else None
        rows = await execute_query(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        mapped = runq.map_run_rows(rows)
        return self._first_row(mapped)

    async def get_run_by_idempotency_key(
        self,
        cliente_id: UUID,
        idempotency_key: str,
        *,
        session: Optional[AsyncSession] = None,
    ) -> Optional[Dict[str, Any]]:
        stmt = runq.select_run_by_idempotency_stmt(cliente_id, idempotency_key)
        if session is not None:
            result = await session.execute(stmt)
            row = result.mappings().first()
            return runq.map_run_row(dict(row)) if row else None
        rows = await execute_query(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        mapped = runq.map_run_rows(rows)
        return self._first_row(mapped)

    async def insert_run(
        self,
        values: Dict[str, Any],
        *,
        session: Optional[AsyncSession] = None,
        cliente_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        stmt = runq.insert_run_stmt(values)
        target_cliente_id = cliente_id or values["cliente_id"]
        if session is not None:
            await session.execute(stmt)
            return values
        await execute_insert(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=target_cliente_id,
        )
        return values

    async def list_steps_for_run(
        self,
        provisioning_run_id: UUID,
        cliente_id: UUID,
        *,
        session: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        stmt = stepq.select_steps_for_run_stmt(provisioning_run_id, cliente_id)
        if session is not None:
            result = await session.execute(stmt)
            rows = [dict(row) for row in result.mappings().all()]
            return stepq.map_step_rows(rows)
        rows = await execute_query(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        return stepq.map_step_rows(rows)

    async def insert_initial_steps_for_run(
        self,
        provisioning_run_id: UUID,
        cliente_id: UUID,
        *,
        session: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        rows = stepq.build_initial_step_rows(
            provisioning_run_id=provisioning_run_id,
            cliente_id=cliente_id,
        )
        for row in rows:
            stmt = stepq.insert_step_stmt(row)
            if session is not None:
                await session.execute(stmt)
            else:
                await execute_insert(
                    stmt,
                    connection_type=DatabaseConnection.ADMIN,
                    client_id=cliente_id,
                )
        return rows

    async def get_cliente_provisioning_snapshot(
        self,
        cliente_id: UUID,
        *,
        session: Optional[AsyncSession] = None,
    ) -> Optional[Dict[str, Any]]:
        stmt = cpsq.select_cliente_provisioning_snapshot_stmt(cliente_id)
        if session is not None:
            result = await session.execute(stmt)
            row = result.mappings().first()
            return cpsq.map_cliente_provisioning_snapshot(dict(row)) if row else None
        rows = await execute_query(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        row = self._first_row(rows)
        return cpsq.map_cliente_provisioning_snapshot(row) if row else None

    async def update_cliente_provisioning_state(
        self,
        *,
        cliente_id: UUID,
        tipo_instalacion: str,
        provisioning_state: Optional[ProvisioningState],
        current_provisioning_run_id: Optional[UUID] = None,
        session: Optional[AsyncSession] = None,
    ) -> None:
        stmt = cpsq.update_cliente_provisioning_state_stmt(
            cliente_id=cliente_id,
            tipo_instalacion=tipo_instalacion,
            provisioning_state=provisioning_state,
            current_provisioning_run_id=current_provisioning_run_id,
        )
        if session is not None:
            await session.execute(stmt)
            return
        await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )

    async def update_run_state(
        self,
        *,
        provisioning_run_id: UUID,
        cliente_id: UUID,
        current_state: ProvisioningState,
        target_state: ProvisioningState,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> int:
        stmt = runq.update_run_state_stmt(
            provisioning_run_id=provisioning_run_id,
            cliente_id=cliente_id,
            current_state=current_state,
            target_state=target_state,
            **kwargs,
        )
        if session is not None:
            result = await session.execute(stmt)
            return int(result.rowcount or 0)
        result = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        if isinstance(result, dict):
            return int(result.get("rows_affected", 0))
        return 0

    async def deactivate_current_runs(
        self,
        cliente_id: UUID,
        *,
        session: Optional[AsyncSession] = None,
    ) -> None:
        stmt = runq.deactivate_current_runs_stmt(cliente_id)
        if session is not None:
            await session.execute(stmt)
            return
        await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )

    async def increment_run_attempt(
        self,
        *,
        provisioning_run_id: UUID,
        cliente_id: UUID,
        attempt_number: int,
        session: Optional[AsyncSession] = None,
    ) -> None:
        stmt = runq.increment_run_attempt_stmt(
            provisioning_run_id=provisioning_run_id,
            cliente_id=cliente_id,
            attempt_number=attempt_number,
        )
        if session is not None:
            await session.execute(stmt)
            return
        await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )

    async def update_run_current_step(
        self,
        *,
        provisioning_run_id: UUID,
        cliente_id: UUID,
        current_step_code: str,
        session: Optional[AsyncSession] = None,
    ) -> int:
        stmt = runq.update_run_current_step_stmt(
            provisioning_run_id=provisioning_run_id,
            cliente_id=cliente_id,
            current_step_code=current_step_code,
        )
        if session is not None:
            result = await session.execute(stmt)
            return int(result.rowcount or 0)
        result = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        if isinstance(result, dict):
            return int(result.get("rows_affected", 0))
        return 0

    async def get_step_by_code(
        self,
        provisioning_run_id: UUID,
        cliente_id: UUID,
        step_code: str,
        *,
        session: Optional[AsyncSession] = None,
    ) -> Optional[Dict[str, Any]]:
        stmt = stepq.select_step_by_code_stmt(
            provisioning_run_id,
            cliente_id,
            step_code,
        )
        if session is not None:
            result = await session.execute(stmt)
            row = result.mappings().first()
            return stepq.map_step_row(dict(row)) if row else None
        rows = await execute_query(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        mapped = stepq.map_step_rows(rows)
        return self._first_row(mapped)

    async def update_step_status(
        self,
        *,
        provisioning_step_id: UUID,
        provisioning_run_id: UUID,
        cliente_id: UUID,
        target_status: Any,
        expected_status: Optional[Any] = None,
        session: Optional[AsyncSession] = None,
        **kwargs: Any,
    ) -> int:
        from app.modules.tenant.application.provisioning import ProvisioningStepStatus

        if not isinstance(target_status, ProvisioningStepStatus):
            target_status = ProvisioningStepStatus(target_status)
        expected = None
        if expected_status is not None:
            expected = (
                expected_status
                if isinstance(expected_status, ProvisioningStepStatus)
                else ProvisioningStepStatus(expected_status)
            )

        stmt = stepq.update_step_status_stmt(
            provisioning_step_id=provisioning_step_id,
            provisioning_run_id=provisioning_run_id,
            cliente_id=cliente_id,
            target_status=target_status,
            expected_status=expected,
            **kwargs,
        )
        if session is not None:
            result = await session.execute(stmt)
            return int(result.rowcount or 0)
        result = await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
        if isinstance(result, dict):
            return int(result.get("rows_affected", 0))
        return 0

    async def reset_steps_from_order(
        self,
        *,
        provisioning_run_id: UUID,
        cliente_id: UUID,
        from_saga_order: int,
        session: Optional[AsyncSession] = None,
    ) -> None:
        stmt = stepq.reset_steps_from_order_stmt(
            provisioning_run_id=provisioning_run_id,
            cliente_id=cliente_id,
            from_saga_order=from_saga_order,
        )
        if session is not None:
            await session.execute(stmt)
            return
        await execute_update(
            stmt,
            connection_type=DatabaseConnection.ADMIN,
            client_id=cliente_id,
        )
