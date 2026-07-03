"""Queries CP — tenant_provisioning_step (PR-F4-01)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, insert, select, update

from app.core.exceptions import ValidationError
from app.infrastructure.database.tables import TenantProvisioningStepTable
from app.modules.tenant.application.provisioning import (
    ProvisioningStepCode,
    ProvisioningStepStatus,
    SAGA_ORDER_BY_CODE,
    SAGA_STEP_ORDER,
    parse_provisioning_step_code,
    parse_provisioning_step_status,
)

_STEP_COLUMNS = {c.name for c in TenantProvisioningStepTable.c}
_STEP_STATUS_VALUES = frozenset(status.value for status in ProvisioningStepStatus)


def _assert_step_status(value: str) -> None:
    if value not in _STEP_STATUS_VALUES:
        raise ValidationError(
            detail=f"step_status inválido: '{value}'",
            internal_code="INVALID_STEP_STATUS",
        )


def build_initial_step_rows(
    *,
    provisioning_run_id: UUID,
    cliente_id: UUID,
) -> List[Dict[str, Any]]:
    """Materializa los 10 steps saga en estado pending (sin ejecutar saga)."""
    rows: List[Dict[str, Any]] = []
    for step_code in SAGA_STEP_ORDER:
        rows.append(
            {
                "provisioning_step_id": uuid4(),
                "provisioning_run_id": provisioning_run_id,
                "cliente_id": cliente_id,
                "step_code": step_code.value,
                "saga_order": SAGA_ORDER_BY_CODE[step_code],
                "step_status": ProvisioningStepStatus.PENDING.value,
            }
        )
    return rows


def insert_step_stmt(values: Dict[str, Any]):
    parse_provisioning_step_code(values["step_code"])
    _assert_step_status(values["step_status"])
    unknown = set(values) - _STEP_COLUMNS
    if unknown:
        raise ValidationError(
            detail=f"Columnas desconocidas en tenant_provisioning_step: {sorted(unknown)}",
            internal_code="INVALID_STEP_COLUMNS",
        )
    return insert(TenantProvisioningStepTable).values(**values)


def select_steps_for_run_stmt(provisioning_run_id: UUID, cliente_id: UUID):
    return (
        select(TenantProvisioningStepTable)
        .where(
            and_(
                TenantProvisioningStepTable.c.provisioning_run_id == provisioning_run_id,
                TenantProvisioningStepTable.c.cliente_id == cliente_id,
            )
        )
        .order_by(TenantProvisioningStepTable.c.saga_order)
    )


def select_step_by_code_stmt(
    provisioning_run_id: UUID,
    cliente_id: UUID,
    step_code: str,
):
    return select(TenantProvisioningStepTable).where(
        and_(
            TenantProvisioningStepTable.c.provisioning_run_id == provisioning_run_id,
            TenantProvisioningStepTable.c.cliente_id == cliente_id,
            TenantProvisioningStepTable.c.step_code == step_code,
        )
    )


def reset_steps_from_order_stmt(
    *,
    provisioning_run_id: UUID,
    cliente_id: UUID,
    from_saga_order: int,
):
    return (
        update(TenantProvisioningStepTable)
        .where(
            and_(
                TenantProvisioningStepTable.c.provisioning_run_id == provisioning_run_id,
                TenantProvisioningStepTable.c.cliente_id == cliente_id,
                TenantProvisioningStepTable.c.saga_order >= from_saga_order,
            )
        )
        .values(
            step_status=ProvisioningStepStatus.PENDING.value,
            started_at=None,
            completed_at=None,
            error_code=None,
            error_message=None,
            idempotency_marker=None,
        )
    )


def update_step_status_stmt(
    *,
    provisioning_step_id: UUID,
    provisioning_run_id: UUID,
    cliente_id: UUID,
    target_status: ProvisioningStepStatus,
    expected_status: Optional[ProvisioningStepStatus] = None,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    idempotency_marker: Optional[str] = None,
):
    _assert_step_status(target_status.value)
    values: Dict[str, Any] = {
        "step_status": target_status.value,
    }
    if started_at is not None:
        values["started_at"] = started_at
    if completed_at is not None:
        values["completed_at"] = completed_at
    if error_code is not None:
        values["error_code"] = error_code
    if error_message is not None:
        values["error_message"] = error_message
    if idempotency_marker is not None:
        values["idempotency_marker"] = idempotency_marker

    conditions = [
        TenantProvisioningStepTable.c.provisioning_step_id == provisioning_step_id,
        TenantProvisioningStepTable.c.provisioning_run_id == provisioning_run_id,
        TenantProvisioningStepTable.c.cliente_id == cliente_id,
    ]
    if expected_status is not None:
        conditions.append(
            TenantProvisioningStepTable.c.step_status == expected_status.value
        )

    return update(TenantProvisioningStepTable).where(and_(*conditions)).values(**values)


def map_step_row(row: Dict[str, Any]) -> Dict[str, Any]:
    if row.get("step_code"):
        parse_provisioning_step_code(row["step_code"])
    if row.get("step_status"):
        parse_provisioning_step_status(row["step_status"])
    return row


def map_step_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [map_step_row(row) for row in rows]
