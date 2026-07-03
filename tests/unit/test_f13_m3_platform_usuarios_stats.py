"""F13-M3 — GET /superadmin/usuarios/stats (estadísticas agregadas globales)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.superadmin.application.services.superadmin_usuario_service import (
    SuperadminUsuarioService,
)

SERVICE = "app.modules.superadmin.application.services.superadmin_usuario_service"
EXECUTE_QUERY = f"{SERVICE}.execute_query"
RESOLVE_KWARGS = f"{SERVICE}.resolve_platform_tenant_data_execute_kwargs"
RESOLVE_DB_TYPE = f"{SERVICE}.resolve_platform_tenant_data_database_type"
REACHABILITY = f"{SERVICE}.check_platform_tenant_reachability"
GET_LEVEL = f"{SERVICE}.UsuarioService.get_user_level_info"
OBTENER_ROLES = f"{SERVICE}.SuperadminUsuarioService._obtener_roles_usuario"
FETCH_CLIENTE = f"{SERVICE}.SuperadminUsuarioService._fetch_cliente_info_from_admin"
GET_USUARIOS_GLOBALES = f"{SERVICE}.SuperadminUsuarioService.get_usuarios_globales"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_stats_returns_all_aggregate_metrics():
    aggregate_row = {
        "total_usuarios": 128,
        "usuarios_activos": 100,
        "usuarios_inactivos": 28,
        "usuarios_bloqueados": 5,
    }

    with patch(EXECUTE_QUERY, new=AsyncMock(return_value=[aggregate_row])):
        result = await SuperadminUsuarioService.obtener_estadisticas_globales_usuarios()

    assert result == {
        "total_usuarios": 128,
        "usuarios_activos": 100,
        "usuarios_inactivos": 28,
        "usuarios_bloqueados": 5,
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_stats_empty_result_returns_zeros():
    with patch(EXECUTE_QUERY, new=AsyncMock(return_value=[])):
        result = await SuperadminUsuarioService.obtener_estadisticas_globales_usuarios()

    assert result == {
        "total_usuarios": 0,
        "usuarios_activos": 0,
        "usuarios_inactivos": 0,
        "usuarios_bloqueados": 0,
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_stats_executes_single_aggregate_query_without_pagination():
    captured_sql: list[str] = []

    async def _execute_query(*args, **kwargs):
        captured_sql.append(str(args[0]))
        return [
            {
                "total_usuarios": 10,
                "usuarios_activos": 7,
                "usuarios_inactivos": 3,
                "usuarios_bloqueados": 1,
            }
        ]

    with patch(EXECUTE_QUERY, side_effect=_execute_query):
        await SuperadminUsuarioService.obtener_estadisticas_globales_usuarios()

    assert len(captured_sql) == 1
    sql = captured_sql[0].upper()
    assert "COUNT(*)" in sql
    assert "ES_ACTIVO = 1" in sql
    assert "ES_ACTIVO = 0" in sql
    assert "FECHA_BLOQUEO IS NOT NULL" in sql
    assert "OFFSET" not in sql
    assert "FETCH" not in sql


@pytest.mark.unit
@pytest.mark.asyncio
async def test_stats_does_not_invoke_enrichment_or_reachability():
    with (
        patch(EXECUTE_QUERY, new=AsyncMock(return_value=[{
            "total_usuarios": 1,
            "usuarios_activos": 1,
            "usuarios_inactivos": 0,
            "usuarios_bloqueados": 0,
        }])),
        patch(REACHABILITY, new=AsyncMock()) as mock_reach,
        patch(OBTENER_ROLES, new=AsyncMock()) as mock_roles,
        patch(GET_LEVEL, new=AsyncMock()) as mock_level,
        patch(FETCH_CLIENTE, new=AsyncMock()) as mock_fetch,
        patch(GET_USUARIOS_GLOBALES, new=AsyncMock()) as mock_list,
    ):
        await SuperadminUsuarioService.obtener_estadisticas_globales_usuarios()

    mock_reach.assert_not_called()
    mock_roles.assert_not_called()
    mock_level.assert_not_called()
    mock_fetch.assert_not_called()
    mock_list.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_stats_total_parity_with_count_usuarios_globales():
    aggregate_row = {
        "total_usuarios": 42,
        "usuarios_activos": 30,
        "usuarios_inactivos": 12,
        "usuarios_bloqueados": 2,
    }

    with (
        patch(EXECUTE_QUERY, new=AsyncMock(return_value=[aggregate_row])),
        patch.object(
            SuperadminUsuarioService,
            "count_usuarios_globales",
            new=AsyncMock(return_value=42),
        ) as mock_count,
    ):
        stats = await SuperadminUsuarioService.obtener_estadisticas_globales_usuarios(
            search="admin",
            proveedor_autenticacion="local",
        )
        total_from_count = await SuperadminUsuarioService.count_usuarios_globales(
            search="admin",
            proveedor_autenticacion="local",
        )

    assert stats["total_usuarios"] == 42
    assert total_from_count == 42
    mock_count.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_stats_mono_tenant_resolves_osr_kwargs_without_enrichment():
    cliente_id = uuid4()
    kwargs = {"connection_type": "default", "client_id": cliente_id}

    async def _execute_query(*args, **kwargs):
        return [
            {
                "total_usuarios": 3,
                "usuarios_activos": 2,
                "usuarios_inactivos": 1,
                "usuarios_bloqueados": 0,
            }
        ]

    with (
        patch(EXECUTE_QUERY, side_effect=_execute_query) as mock_exec,
        patch(RESOLVE_KWARGS, new=AsyncMock(return_value=kwargs)),
        patch(RESOLVE_DB_TYPE, new=AsyncMock(return_value="single")),
        patch(
            f"{SERVICE}.ClienteService.obtener_cliente_por_id",
            new=AsyncMock(
                return_value=type(
                    "C",
                    (),
                    {
                        "cliente_id": cliente_id,
                        "razon_social": "Acme",
                        "subdominio": "acme",
                        "codigo_cliente": "ACM",
                        "nombre_comercial": None,
                        "es_activo": True,
                    },
                )()
            ),
        ),
        patch(REACHABILITY, new=AsyncMock()) as mock_reach,
    ):
        result = await SuperadminUsuarioService.obtener_estadisticas_globales_usuarios(
            cliente_id=cliente_id,
        )

    assert result["total_usuarios"] == 3
    mock_reach.assert_not_called()
    mock_exec.assert_called_once()
    assert mock_exec.call_args.kwargs == kwargs
