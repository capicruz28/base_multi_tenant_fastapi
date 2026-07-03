"""PR-F4-01 — validación ORM tablas provisioning vs DDL."""
from __future__ import annotations

from typing import AbstractSet

import pytest
from sqlalchemy import CheckConstraint, UniqueConstraint

from app.infrastructure.database.tables import (
    ClienteTable,
    TenantProvisioningRunTable,
    TenantProvisioningStepTable,
)

RUN_COLUMNS: AbstractSet[str] = {
    "provisioning_run_id",
    "cliente_id",
    "provisioning_state",
    "is_current",
    "attempt_number",
    "idempotency_key",
    "current_step_code",
    "started_at",
    "updated_at",
    "ready_at",
    "failed_at",
    "last_error_code",
    "last_error_message",
    "created_by_usuario_id",
}

STEP_COLUMNS: AbstractSet[str] = {
    "provisioning_step_id",
    "provisioning_run_id",
    "cliente_id",
    "step_code",
    "saga_order",
    "step_status",
    "started_at",
    "completed_at",
    "error_code",
    "error_message",
    "idempotency_marker",
}

CLIENTE_PROVISIONING_COLUMNS: AbstractSet[str] = {
    "provisioning_state",
    "current_provisioning_run_id",
}

RUN_INDEXES = {
    "IDX_tpr_cliente",
}

STEP_INDEXES = {
    "IDX_tps_run_order",
    "IDX_tps_cliente",
}


def _column_names(table) -> AbstractSet[str]:
    return {column.name for column in table.c}


def _index_names(table) -> AbstractSet[str]:
    return {index.name for index in table.indexes if index.name}


def _check_constraint_names(table) -> AbstractSet[str]:
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name
    }


def _unique_constraint_names(table) -> AbstractSet[str]:
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint) and constraint.name
    }


@pytest.mark.unit
def test_f4_01_run_columns_match_ddl():
    assert _column_names(TenantProvisioningRunTable) == RUN_COLUMNS


@pytest.mark.unit
def test_f4_01_step_columns_match_ddl():
    assert _column_names(TenantProvisioningStepTable) == STEP_COLUMNS


@pytest.mark.unit
def test_f4_01_cliente_provisioning_columns_present():
    assert CLIENTE_PROVISIONING_COLUMNS.issubset(_column_names(ClienteTable))


@pytest.mark.unit
def test_f4_01_run_check_constraints():
    assert _check_constraint_names(TenantProvisioningRunTable) == {
        "CK_tpr_provisioning_state",
    }


@pytest.mark.unit
def test_f4_01_step_check_constraints():
    assert _check_constraint_names(TenantProvisioningStepTable) == {
        "CK_tps_step_code",
        "CK_tps_step_status",
    }


@pytest.mark.unit
def test_f4_01_cliente_provisioning_check_constraint():
    assert "CK_cliente_provisioning_state" in _check_constraint_names(ClienteTable)


@pytest.mark.unit
def test_f4_01_step_unique_run_step():
    assert _unique_constraint_names(TenantProvisioningStepTable) == {
        "UQ_tps_run_step",
    }


@pytest.mark.unit
def test_f4_01_run_indexes():
    assert _index_names(TenantProvisioningRunTable) == RUN_INDEXES


@pytest.mark.unit
def test_f4_01_step_indexes():
    assert _index_names(TenantProvisioningStepTable) == STEP_INDEXES


@pytest.mark.unit
def test_f4_01_cliente_provisioning_index():
    assert "IDX_cliente_provisioning_state" in _index_names(ClienteTable)


@pytest.mark.unit
def test_f4_01_foreign_keys_defined():
    run_fks = {fk.parent.name for fk in TenantProvisioningRunTable.foreign_keys}
    assert run_fks == {"cliente_id"}

    step_fks = {fk.parent.name for fk in TenantProvisioningStepTable.foreign_keys}
    assert step_fks == {"provisioning_run_id", "cliente_id"}

    cliente_run_fk = {
        fk.parent.name
        for fk in ClienteTable.foreign_keys
        if fk.parent.name == "current_provisioning_run_id"
    }
    assert cliente_run_fk == {"current_provisioning_run_id"}


@pytest.mark.unit
def test_f4_01_tables_exported_from_tables_module():
    from app.infrastructure.database import tables as tables_module

    assert "TenantProvisioningRunTable" in tables_module.__all__
    assert "TenantProvisioningStepTable" in tables_module.__all__
