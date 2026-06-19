"""IAM-PA-001: filtros vigencia PA-004 en usuarios/roles + POST reactivate usuario."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.database.queries.rbac.rbac_queries import (
    COUNT_ROLES_PAGINATED,
    SELECT_ROLES_PAGINATED,
)
from app.infrastructure.database.queries.users.user_queries import (
    COUNT_USUARIOS_PAGINATED,
    SELECT_USUARIOS_PAGINATED,
)
from app.modules.rbac.application.services.rol_service import RolService
from app.modules.users.application.services.user_service import UsuarioService
from app.shared.vigencia_filters import VIGENCIA_ES_ACTIVO_CLAUSE, vigencia_bind_params

CLIENTE_ID = UUID("e4c8e906-0e64-4f4e-a04d-8daee57dc7f8")
NOW = datetime(2026, 1, 15, 10, 0, 0)


def _tenant_context(database_type: str = "single") -> MagicMock:
    ctx = MagicMock()
    ctx.database_type = database_type
    return ctx


def test_vigencia_bind_params_pa004_precedence():
    assert vigencia_bind_params(True, False) == {"solo_activos": 1, "solo_inactivos": 0}
    assert vigencia_bind_params(False, True) == {"solo_activos": 0, "solo_inactivos": 1}
    assert vigencia_bind_params(False, False) == {"solo_activos": 0, "solo_inactivos": 0}
    assert vigencia_bind_params(True, True) == {"solo_activos": 0, "solo_inactivos": 1}


def test_user_queries_include_vigencia_clause():
    clause = VIGENCIA_ES_ACTIVO_CLAUSE.format(alias="u")
    assert clause in SELECT_USUARIOS_PAGINATED
    assert clause in COUNT_USUARIOS_PAGINATED
    assert "solo_inactivos" in SELECT_USUARIOS_PAGINATED
    assert "es_eliminado = 0" in SELECT_USUARIOS_PAGINATED


def test_role_queries_include_vigencia_clause():
    clause = VIGENCIA_ES_ACTIVO_CLAUSE.format(alias="r")
    assert clause in SELECT_ROLES_PAGINATED
    assert clause in COUNT_ROLES_PAGINATED
    assert "solo_inactivos" in SELECT_ROLES_PAGINATED
    assert "solo_activos" in COUNT_ROLES_PAGINATED


@pytest.mark.asyncio
async def test_usuarios_propagates_solo_inactivos_to_queries():
    mock_query = AsyncMock(
        side_effect=[
            [{"": 0}],
            [],
        ]
    )
    with (
        patch(
            "app.core.tenant.context.try_get_tenant_context",
            return_value=_tenant_context("single"),
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_query",
            mock_query,
        ),
    ):
        await UsuarioService.get_usuarios_paginated(
            cliente_id=CLIENTE_ID,
            page=1,
            limit=10,
            solo_activos=True,
            solo_inactivos=True,
        )

    count_params = mock_query.await_args_list[0][0][0].compile().params
    assert count_params["solo_inactivos"] == 1
    assert count_params["solo_activos"] == 0


@pytest.mark.asyncio
async def test_roles_propagates_solo_activos_false_to_queries():
    mock_query = AsyncMock(return_value=[{"total": 0}])
    with (
        patch(
            "app.core.tenant.context.try_get_tenant_context",
            return_value=_tenant_context("single"),
        ),
        patch(
            "app.modules.rbac.application.services.rol_service.execute_query",
            mock_query,
        ),
    ):
        await RolService.obtener_roles_paginados(
            cliente_id=CLIENTE_ID,
            page=1,
            limit=10,
            solo_activos=False,
            solo_inactivos=False,
        )

    count_params = mock_query.await_args_list[0][0][0].compile().params
    assert count_params["solo_activos"] == 0
    assert count_params["solo_inactivos"] == 0


@pytest.mark.asyncio
async def test_reactivar_usuario_sets_eliminado_and_activo():
    usuario_id = uuid4()
    usuario_eliminado = {
        "usuario_id": usuario_id,
        "cliente_id": CLIENTE_ID,
        "es_eliminado": True,
        "es_activo": False,
    }
    usuario_activo = {
        "usuario_id": usuario_id,
        "cliente_id": CLIENTE_ID,
        "nombre_usuario": "reactivado",
        "correo": "r@test.com",
        "nombre": "R",
        "apellido": "T",
        "es_activo": True,
        "correo_confirmado": True,
        "fecha_creacion": NOW,
        "fecha_ultimo_acceso": None,
        "fecha_actualizacion": NOW,
    }

    usuario_revisado = {
        **usuario_eliminado,
        "es_eliminado": False,
        "es_activo": True,
    }

    with (
        patch.object(
            UsuarioService,
            "obtener_usuario_incluyendo_eliminados",
            new_callable=AsyncMock,
            side_effect=[usuario_eliminado, usuario_revisado],
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_update",
            new_callable=AsyncMock,
            return_value={"usuario_id": usuario_id},
        ),
        patch.object(
            UsuarioService,
            "obtener_usuario_por_id",
            new_callable=AsyncMock,
            return_value=usuario_activo,
        ),
    ):
        result = await UsuarioService.reactivar_usuario(
            cliente_id=CLIENTE_ID,
            usuario_id=usuario_id,
        )

    assert result["es_activo"] is True
    assert result["usuario_id"] == usuario_id


@pytest.mark.asyncio
async def test_reactivar_usuario_idempotent_when_already_active():
    usuario_id = uuid4()
    usuario_activo = {
        "usuario_id": usuario_id,
        "cliente_id": CLIENTE_ID,
        "es_eliminado": False,
        "es_activo": True,
    }
    read_back = {**usuario_activo, "nombre_usuario": "ok", "correo": "a@b.com"}

    with (
        patch.object(
            UsuarioService,
            "obtener_usuario_incluyendo_eliminados",
            new_callable=AsyncMock,
            return_value=usuario_activo,
        ),
        patch.object(
            UsuarioService,
            "obtener_usuario_por_id",
            new_callable=AsyncMock,
            return_value=read_back,
        ),
        patch(
            "app.modules.users.application.services.user_service.execute_update",
            new_callable=AsyncMock,
        ) as mock_update,
    ):
        result = await UsuarioService.reactivar_usuario(
            cliente_id=CLIENTE_ID,
            usuario_id=usuario_id,
        )

    mock_update.assert_not_called()
    assert result["nombre_usuario"] == "ok"


def test_openapi_includes_iam_pa001_params():
    from app.main import app

    schema = TestClient(app).get("/openapi.json").json()
    usuarios_params = {
        p["name"]
        for p in schema["paths"]["/api/v1/usuarios/"]["get"]["parameters"]
        if p.get("in") == "query"
    }
    roles_params = {
        p["name"]
        for p in schema["paths"]["/api/v1/roles/"]["get"]["parameters"]
        if p.get("in") == "query"
    }
    assert "solo_activos" in usuarios_params
    assert "solo_inactivos" in usuarios_params
    assert "solo_activos" in roles_params
    assert "solo_inactivos" in roles_params
    assert "/api/v1/usuarios/{usuario_id}/reactivate/" in schema["paths"]
