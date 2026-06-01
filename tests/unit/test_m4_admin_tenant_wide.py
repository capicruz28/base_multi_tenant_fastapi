"""
Tests M4 — ADMIN_TENANT tenant-wide (Modelo B).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.auth.application.services.auth_service import AuthService
from app.modules.tenant.application.services.minimal_erp_tenant_bootstrap_service import (
    MinimalErpTenantBootstrapService,
)


def _empresa_row(empresa_id, nombre="Empresa"):
    return {
        "empresa_id": empresa_id,
        "razon_social": nombre,
        "nombre_comercial": None,
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_vincular_admin_empresa_sets_null_scope_m4():
    session = AsyncMock()
    cliente_id = uuid4()
    usuario_id = uuid4()
    admin_rol_id = uuid4()
    empresa_id = uuid4()

    session.execute = AsyncMock(return_value=MagicMock(rowcount=1))

    result = await MinimalErpTenantBootstrapService.vincular_admin_empresa(
        session,
        cliente_id=cliente_id,
        usuario_id=usuario_id,
        admin_rol_id=admin_rol_id,
        empresa_id=empresa_id,
    )

    assert result["usuario_rol_empresa_id"] is None
    assert result["empresa_default_id"] == str(empresa_id)
    assert session.execute.await_count >= 2

    update_ur_sql = str(session.execute.await_args_list[1][0][0])
    assert "empresa_id = NULL" in update_ur_sql
    assert "SET empresa_id = :empresa_id" not in update_ur_sql.replace(
        "empresa_default_id", ""
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_vincular_admin_inserts_null_when_no_row():
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(rowcount=1),
            MagicMock(rowcount=0),
            MagicMock(rowcount=1),
        ]
    )

    await MinimalErpTenantBootstrapService.vincular_admin_empresa(
        session,
        cliente_id=uuid4(),
        usuario_id=uuid4(),
        admin_rol_id=uuid4(),
        empresa_id=uuid4(),
    )

    insert_call = session.execute.await_args_list[2][0][0]
    insert_sql = str(insert_call)
    assert "NULL, 1" in insert_sql or "NULL" in insert_sql


@pytest.mark.unit
@pytest.mark.asyncio
async def test_admin_tenant_wide_login_elegibles_from_org():
    """Admin global (NULL ur) + 2 org → requiere selección sin default (M1 + M4)."""
    usuario_id = uuid4()
    cliente_id = uuid4()
    emp1, emp2 = uuid4(), uuid4()

    with patch.object(
        AuthService,
        "_listar_empresas_activas_org",
        new=AsyncMock(
            return_value=[_empresa_row(emp1, "A"), _empresa_row(emp2, "B")]
        ),
    ), patch(
        "app.modules.auth.application.services.auth_service.execute_query",
        new=AsyncMock(
            side_effect=[
                [],
                [{"admin_sin_empresa_count": 1}],
                [{"empresa_default_id": None}],
            ]
        ),
    ):
        result = await AuthService.get_empresa_activa_para_login(
            usuario_id, cliente_id
        )

    assert result["es_admin_sin_empresa"] is True
    assert len(result["empresas_disponibles"]) == 2
    assert result["requiere_seleccion"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_admin_tenant_wide_single_org_direct_session():
    usuario_id = uuid4()
    cliente_id = uuid4()
    emp1 = uuid4()

    with patch.object(
        AuthService,
        "_listar_empresas_activas_org",
        new=AsyncMock(return_value=[_empresa_row(emp1)]),
    ), patch(
        "app.modules.auth.application.services.auth_service.execute_query",
        new=AsyncMock(
            side_effect=[
                [],
                [{"admin_sin_empresa_count": 1}],
                [{"empresa_default_id": emp1}],
            ]
        ),
    ):
        result = await AuthService.get_empresa_activa_para_login(
            usuario_id, cliente_id
        )

    assert result["requiere_seleccion"] is False
    assert result["empresa_activa"] == emp1


@pytest.mark.unit
def test_sql_empresa_filter_includes_global_roles():
    from app.core.tenant.empresa_context import sql_empresa_filter_usuario_rol

    fragment = sql_empresa_filter_usuario_rol("ur")
    assert "ur.empresa_id IS NULL" in fragment
    assert "ur.empresa_id = :empresa_id" in fragment
