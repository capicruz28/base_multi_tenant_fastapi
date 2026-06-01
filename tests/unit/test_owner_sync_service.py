"""Tests OwnerSyncService v1.0 (M1)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import DatabaseError
from app.modules.tenant.application.services.owner_sync_constants import (
    OWNER_SYNC_ZERO_GRANTS,
)
from app.modules.tenant.application.services.owner_sync_service import OwnerSyncService


def _mock_scalar(value):
    result = MagicMock()
    result.fetchone.return_value = (value,)
    return result


def _mock_rows(rows):
    result = MagicMock()
    result.fetchall.return_value = rows
    return result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_module_inserts_rp_and_rmp():
    session = AsyncMock()
    cliente_id = uuid4()
    admin_rol_id = uuid4()

    async def execute_side_effect(*args, **kwargs):
        sql = str(args[0])
        result = MagicMock()
        if "cliente_modulo cm" in sql and "esta_activo" in sql:
            result.fetchone.return_value = (1,)
        elif "FROM modulo" in sql and "es_activo" in sql and "codigo" in sql:
            result.fetchone.return_value = (1,)
        elif "INSERT INTO rol_permiso" in sql:
            return MagicMock()
        elif "INSERT INTO rol_menu_permiso" in sql:
            return MagicMock()
        elif "COUNT(*)" in sql and "rol_permiso" in sql:
            result.fetchone.return_value = (5,)
        elif "COUNT(*)" in sql and "rol_menu_permiso" in sql:
            result.fetchone.return_value = (4,)
        elif "SELECT mm.codigo" in sql:
            result.fetchall.return_value = [("CRM_LEADS",)]
        elif "SELECT p.codigo" in sql and "rol_permiso" in sql:
            result.fetchall.return_value = [("crm.lead.leer",)]
        else:
            result.fetchone.return_value = (0,)
            result.fetchall.return_value = []
        return result

    session.execute = AsyncMock(side_effect=execute_side_effect)

    result = await OwnerSyncService.sync_module_for_owner(
        session,
        cliente_id=cliente_id,
        modulo_codigo="CRM",
        admin_rol_id=admin_rol_id,
    )

    assert result.modulo_codigo == "CRM"
    assert result.rol_permiso_total_module == 5
    assert result.rol_menu_permiso_total_module == 4


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_sys_admin_menu_filter():
    session = AsyncMock()
    captured_sql: list[str] = []

    async def execute_side_effect(*args, **kwargs):
        sql = str(args[0])
        captured_sql.append(sql)
        result = MagicMock()
        if "cliente_modulo cm" in sql:
            result.fetchone.return_value = (1,)
        elif "FROM modulo" in sql and "codigo" in sql:
            result.fetchone.return_value = (1,)
        elif "INSERT INTO rol_menu_permiso" in sql:
            return MagicMock()
        elif "COUNT(*)" in sql:
            result.fetchone.return_value = (3,)
        else:
            result.fetchall.return_value = []
            result.fetchone.return_value = (1,)
        return result

    session.execute = AsyncMock(side_effect=execute_side_effect)

    await OwnerSyncService.sync_module_for_owner(
        session,
        cliente_id=uuid4(),
        modulo_codigo="SYS_ADMIN",
        admin_rol_id=uuid4(),
    )

    rmp_insert = next(s for s in captured_sql if "INSERT INTO rol_menu_permiso" in s)
    assert "SYS_ADMIN.TENANT." in rmp_insert
    assert "SYS_ADMIN.PLATFORM." in rmp_insert


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_zero_grants_raises():
    session = AsyncMock()

    async def execute_side_effect(*args, **kwargs):
        sql = str(args[0])
        result = MagicMock()
        if "cliente_modulo cm" in sql and "SELECT 1" in sql:
            result.fetchone.return_value = (1,)
        elif "FROM modulo" in sql and "codigo = :modulo_codigo" in sql:
            result.fetchone.return_value = (1,)
        elif "INSERT INTO rol_permiso" in sql or "INSERT INTO rol_menu_permiso" in sql:
            return MagicMock()
        elif "COUNT(*)" in sql and "rol_permiso rp" in sql:
            result.fetchone.return_value = (0,)
        elif "COUNT(*)" in sql and "rol_menu_permiso rmp" in sql:
            result.fetchone.return_value = (0,)
        else:
            result.fetchall.return_value = []
            result.fetchone.return_value = (0,)
        return result

    session.execute = AsyncMock(side_effect=execute_side_effect)

    with pytest.raises(DatabaseError) as exc:
        await OwnerSyncService.sync_module_for_owner(
            session,
            cliente_id=uuid4(),
            modulo_codigo="CRM",
            admin_rol_id=uuid4(),
        )
    assert exc.value.internal_code == OWNER_SYNC_ZERO_GRANTS


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_idempotent_second_run_zero_inserts():
    session = AsyncMock()
    call_counts = {"rp": 0, "rmp": 0}

    async def execute_side_effect(*args, **kwargs):
        sql = str(args[0])
        result = MagicMock()
        if "cliente_modulo" in sql or ("modulo" in sql and "codigo" in sql):
            result.fetchone.return_value = (1,)
        elif "INSERT INTO rol_permiso" in sql:
            call_counts["rp"] += 1
            return MagicMock()
        elif "INSERT INTO rol_menu_permiso" in sql:
            call_counts["rmp"] += 1
            return MagicMock()
        elif "COUNT(*)" in sql and "rol_permiso" in sql:
            result.fetchone.return_value = (3,)
        elif "COUNT(*)" in sql:
            result.fetchone.return_value = (4,)
        else:
            result.fetchall.return_value = []
        return result

    session.execute = AsyncMock(side_effect=execute_side_effect)

    result = await OwnerSyncService.sync_module_for_owner(
        session,
        cliente_id=uuid4(),
        modulo_codigo="INV",
        admin_rol_id=uuid4(),
    )
    assert result.rol_permiso_inserted == 0
    assert result.rol_menu_permiso_inserted == 0
