"""Queries CP — denormalización provisioning en cliente (PR-F4-01)."""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import and_, select, update

from app.core.exceptions import ValidationError
from app.infrastructure.database.tables import ClienteTable
from app.modules.tenant.application.provisioning import (
    ProvisioningState,
    assert_cliente_provisioning_profile,
    parse_provisioning_state,
)

_CLIENTE_PROVISIONING_COLUMNS = frozenset(
    {
        "provisioning_state",
        "current_provisioning_run_id",
        "tipo_instalacion",
        "cliente_id",
    }
)


def select_cliente_provisioning_snapshot_stmt(cliente_id: UUID):
    return select(
        ClienteTable.c.cliente_id,
        ClienteTable.c.tipo_instalacion,
        ClienteTable.c.provisioning_state,
        ClienteTable.c.current_provisioning_run_id,
    ).where(ClienteTable.c.cliente_id == cliente_id)


def update_cliente_provisioning_state_stmt(
    *,
    cliente_id: UUID,
    tipo_instalacion: str,
    provisioning_state: Optional[ProvisioningState],
    current_provisioning_run_id: Optional[UUID] = None,
):
    state_value = provisioning_state.value if provisioning_state else None
    assert_cliente_provisioning_profile(
        tipo_instalacion=tipo_instalacion,
        provisioning_state=state_value,
    )
    if state_value is not None:
        parse_provisioning_state(state_value)

    values: Dict[str, Any] = {
        "provisioning_state": state_value,
    }
    if current_provisioning_run_id is not None or provisioning_state is None:
        values["current_provisioning_run_id"] = current_provisioning_run_id

    return (
        update(ClienteTable)
        .where(ClienteTable.c.cliente_id == cliente_id)
        .values(**values)
    )


def map_cliente_provisioning_snapshot(row: Dict[str, Any]) -> Dict[str, Any]:
    if not row:
        raise ValidationError(
            detail="Snapshot provisioning cliente vacío.",
            internal_code="EMPTY_CLIENTE_PROVISIONING_SNAPSHOT",
        )
    missing = _CLIENTE_PROVISIONING_COLUMNS - set(row)
    if missing:
        raise ValidationError(
            detail=f"Snapshot provisioning incompleto: faltan {sorted(missing)}",
            internal_code="INCOMPLETE_CLIENTE_PROVISIONING_SNAPSHOT",
        )
    assert_cliente_provisioning_profile(
        tipo_instalacion=row["tipo_instalacion"],
        provisioning_state=row.get("provisioning_state"),
    )
    return row
