"""Queries CP — tenant_provisioning_run (PR-F4-01)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, insert, select, update

from app.core.exceptions import ValidationError
from app.infrastructure.database.tables import TenantProvisioningRunTable
from app.modules.tenant.application.provisioning import (
    ProvisioningState,
    assert_provisioning_state_transition,
    parse_provisioning_state,
    parse_provisioning_step_code,
)

_RUN_COLUMNS = {c.name for c in TenantProvisioningRunTable.c}
_PROVISIONING_STATE_VALUES = frozenset(
    state.value for state in ProvisioningState
)


def _assert_run_provisioning_state(value: str) -> None:
    if value not in _PROVISIONING_STATE_VALUES:
        raise ValidationError(
            detail=f"provisioning_state inválido en run: '{value}'",
            internal_code="INVALID_RUN_PROVISIONING_STATE",
        )


def build_run_insert_values(
    *,
    cliente_id: UUID,
    provisioning_state: ProvisioningState,
    provisioning_run_id: Optional[UUID] = None,
    attempt_number: int = 1,
    idempotency_key: Optional[str] = None,
    current_step_code: Optional[str] = None,
    created_by_usuario_id: Optional[UUID] = None,
    is_current: bool = True,
) -> Dict[str, Any]:
    assert_provisioning_state_transition(None, provisioning_state)
    return {
        "provisioning_run_id": provisioning_run_id or uuid4(),
        "cliente_id": cliente_id,
        "provisioning_state": provisioning_state.value,
        "is_current": is_current,
        "attempt_number": attempt_number,
        "idempotency_key": idempotency_key,
        "current_step_code": current_step_code,
        "created_by_usuario_id": created_by_usuario_id,
    }


def insert_run_stmt(values: Dict[str, Any]):
    _assert_run_provisioning_state(values["provisioning_state"])
    unknown = set(values) - _RUN_COLUMNS
    if unknown:
        raise ValidationError(
            detail=f"Columnas desconocidas en tenant_provisioning_run: {sorted(unknown)}",
            internal_code="INVALID_RUN_COLUMNS",
        )
    return insert(TenantProvisioningRunTable).values(**values)


def select_run_by_id_stmt(provisioning_run_id: UUID, cliente_id: UUID):
    return select(TenantProvisioningRunTable).where(
        and_(
            TenantProvisioningRunTable.c.provisioning_run_id == provisioning_run_id,
            TenantProvisioningRunTable.c.cliente_id == cliente_id,
        )
    )


def select_current_run_for_cliente_stmt(cliente_id: UUID):
    return (
        select(TenantProvisioningRunTable)
        .where(
            and_(
                TenantProvisioningRunTable.c.cliente_id == cliente_id,
                TenantProvisioningRunTable.c.is_current == True,  # noqa: E712
            )
        )
        .order_by(TenantProvisioningRunTable.c.started_at.desc())
    )


def select_run_by_idempotency_stmt(cliente_id: UUID, idempotency_key: str):
    return select(TenantProvisioningRunTable).where(
        and_(
            TenantProvisioningRunTable.c.cliente_id == cliente_id,
            TenantProvisioningRunTable.c.idempotency_key == idempotency_key,
        )
    )


def deactivate_current_runs_stmt(cliente_id: UUID):
    return (
        update(TenantProvisioningRunTable)
        .where(
            and_(
                TenantProvisioningRunTable.c.cliente_id == cliente_id,
                TenantProvisioningRunTable.c.is_current == True,  # noqa: E712
            )
        )
        .values(is_current=False, updated_at=datetime.utcnow())
    )


def increment_run_attempt_stmt(
    *,
    provisioning_run_id: UUID,
    cliente_id: UUID,
    attempt_number: int,
):
    return (
        update(TenantProvisioningRunTable)
        .where(
            and_(
                TenantProvisioningRunTable.c.provisioning_run_id == provisioning_run_id,
                TenantProvisioningRunTable.c.cliente_id == cliente_id,
            )
        )
        .values(
            attempt_number=attempt_number,
            updated_at=datetime.utcnow(),
            failed_at=None,
            last_error_code=None,
            last_error_message=None,
        )
    )


def update_run_current_step_stmt(
    *,
    provisioning_run_id: UUID,
    cliente_id: UUID,
    current_step_code: str,
):
    parse_provisioning_step_code(current_step_code)
    return (
        update(TenantProvisioningRunTable)
        .where(
            and_(
                TenantProvisioningRunTable.c.provisioning_run_id == provisioning_run_id,
                TenantProvisioningRunTable.c.cliente_id == cliente_id,
                TenantProvisioningRunTable.c.provisioning_state == ProvisioningState.PROVISIONING.value,
            )
        )
        .values(
            current_step_code=current_step_code,
            updated_at=datetime.utcnow(),
        )
    )


def update_run_state_stmt(
    *,
    provisioning_run_id: UUID,
    cliente_id: UUID,
    target_state: ProvisioningState,
    current_state: ProvisioningState,
    current_step_code: Optional[str] = None,
    last_error_code: Optional[str] = None,
    last_error_message: Optional[str] = None,
    ready_at: Optional[datetime] = None,
    failed_at: Optional[datetime] = None,
):
    assert_provisioning_state_transition(current_state, target_state)
    values: Dict[str, Any] = {
        "provisioning_state": target_state.value,
        "updated_at": datetime.utcnow(),
    }
    if current_step_code is not None:
        values["current_step_code"] = current_step_code
    if last_error_code is not None:
        values["last_error_code"] = last_error_code
    if last_error_message is not None:
        values["last_error_message"] = last_error_message
    if ready_at is not None:
        values["ready_at"] = ready_at
    if failed_at is not None:
        values["failed_at"] = failed_at

    return (
        update(TenantProvisioningRunTable)
        .where(
            and_(
                TenantProvisioningRunTable.c.provisioning_run_id == provisioning_run_id,
                TenantProvisioningRunTable.c.cliente_id == cliente_id,
                TenantProvisioningRunTable.c.provisioning_state == current_state.value,
            )
        )
        .values(**values)
    )


def map_run_row(row: Dict[str, Any]) -> Dict[str, Any]:
    if row.get("provisioning_state"):
        parse_provisioning_state(row["provisioning_state"])
    return row


def map_run_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [map_run_row(row) for row in rows]
