"""F13-M2 — paridad count_usuarios_globales vs get_usuarios_globales."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.modules.superadmin.application.services.superadmin_usuario_service import (
    SuperadminUsuarioService,
)
from app.modules.superadmin.presentation.schemas import ClienteInfo, RolInfo
from tests.integration.helpers.hybrid_mock_metadata import (
    HYBRID_FIXTURE_TENANT_DEDICATED,
    HYBRID_FIXTURE_TENANT_SHARED,
)

SERVICE = "app.modules.superadmin.application.services.superadmin_usuario_service"
EXECUTE_QUERY = f"{SERVICE}.execute_query"
RESOLVE_KWARGS = f"{SERVICE}.resolve_platform_tenant_data_execute_kwargs"
RESOLVE_DB_TYPE = f"{SERVICE}.resolve_platform_tenant_data_database_type"
REACHABILITY = f"{SERVICE}.check_platform_tenant_reachability"
GET_LEVEL = f"{SERVICE}.UsuarioService.get_user_level_info"
OBTENER_ROLES = f"{SERVICE}.SuperadminUsuarioService._obtener_roles_usuario"
FETCH_CLIENTE = f"{SERVICE}.SuperadminUsuarioService._fetch_cliente_info_from_admin"


def _usuario_row(usuario_id: UUID, cliente_id: UUID) -> dict:
    return {
        "usuario_id": usuario_id,
        "cliente_id": cliente_id,
        "nombre_usuario": f"user-{usuario_id.hex[:8]}",
        "correo": "user@example.com",
        "nombre": "Test",
        "apellido": "User",
        "dni": None,
        "telefono": None,
        "es_activo": 1,
        "es_eliminado": 0,
        "proveedor_autenticacion": "local",
        "referencia_externa_id": None,
        "referencia_externa_email": None,
        "correo_confirmado": 1,
        "intentos_fallidos": 0,
        "fecha_bloqueo": None,
        "ultimo_ip": None,
        "fecha_creacion": datetime(2026, 1, 1, 12, 0, 0),
        "fecha_ultimo_acceso": None,
        "fecha_actualizacion": None,
        "sincronizado_desde": None,
        "fecha_ultima_sincronizacion": None,
    }


def _cliente_info(cliente_id: UUID, subdominio: str) -> ClienteInfo:
    return ClienteInfo(
        cliente_id=cliente_id,
        razon_social=f"{subdominio} SA",
        subdominio=subdominio,
        codigo_cliente=subdominio.upper(),
        nombre_comercial=None,
        tipo_instalacion="shared" if subdominio == "shared" else "dedicated",
        estado_suscripcion="activo",
    )


@pytest.fixture
def mock_global_list_execute():
    shared_user = uuid4()
    dedicated_user = uuid4()
    rows = [
        _usuario_row(shared_user, HYBRID_FIXTURE_TENANT_SHARED),
        _usuario_row(dedicated_user, HYBRID_FIXTURE_TENANT_DEDICATED),
    ]

    async def _execute_query(*args, **kwargs):
        sql = str(args[0]) if args else ""
        if "COUNT(*)" in sql:
            return [{"total": len(rows)}]
        return rows

    with patch(EXECUTE_QUERY, new=AsyncMock(side_effect=_execute_query)):
        yield {"rows": rows, "total": len(rows)}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_equals_list_total_global(mock_global_list_execute):
    from app.core.tenant.platform_tenant_reachability import ReachabilityResult, ReachabilityStatus

    async def _reachability(cliente_id, **_kwargs):
        return ReachabilityResult(
            cliente_id=cliente_id,
            status=ReachabilityStatus.REACHABLE,
            metadata={"database_type": "single"},
        )

    with patch(REACHABILITY, new=AsyncMock(side_effect=_reachability)), patch(
        FETCH_CLIENTE,
        new=AsyncMock(side_effect=lambda cid: _cliente_info(cid, "shared")),
    ), patch(OBTENER_ROLES, new=AsyncMock(return_value=[])), patch(
        GET_LEVEL,
        new=AsyncMock(
            return_value={"access_level": 1, "is_super_admin": False, "user_type": "user"}
        ),
    ):
        total = await SuperadminUsuarioService.count_usuarios_globales()
        result = await SuperadminUsuarioService.get_usuarios_globales(limit=100)

    assert total == mock_global_list_execute["total"]
    assert result["total_usuarios"] == total


@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_and_list_share_where_builder(mock_global_list_execute):
    from app.core.tenant.platform_tenant_reachability import ReachabilityResult, ReachabilityStatus

    build_calls: list[dict] = []
    original_build = SuperadminUsuarioService._build_usuarios_globales_where

    def _spy_build(**kwargs):
        build_calls.append(kwargs)
        return original_build(**kwargs)

    kwargs_calls: list[UUID | None] = []
    original_kwargs = SuperadminUsuarioService._resolve_usuarios_globales_query_kwargs

    async def _spy_kwargs(cliente_id):
        kwargs_calls.append(cliente_id)
        return await original_kwargs(cliente_id)

    async def _reachability(cliente_id, **_kwargs):
        return ReachabilityResult(
            cliente_id=cliente_id,
            status=ReachabilityStatus.REACHABLE,
            metadata={"database_type": "single"},
        )

    filter_kwargs = {
        "search": "acme",
        "es_activo": True,
        "proveedor_autenticacion": "local",
        "ordenar_por": "nombre_usuario",
        "orden": "asc",
    }

    with patch.object(
        SuperadminUsuarioService,
        "_build_usuarios_globales_where",
        side_effect=_spy_build,
    ), patch.object(
        SuperadminUsuarioService,
        "_resolve_usuarios_globales_query_kwargs",
        side_effect=_spy_kwargs,
    ), patch(REACHABILITY, new=AsyncMock(side_effect=_reachability)), patch(
        FETCH_CLIENTE,
        new=AsyncMock(return_value=_cliente_info(HYBRID_FIXTURE_TENANT_SHARED, "shared")),
    ), patch(OBTENER_ROLES, new=AsyncMock(return_value=[])), patch(
        GET_LEVEL,
        new=AsyncMock(
            return_value={"access_level": 1, "is_super_admin": False, "user_type": "user"}
        ),
    ):
        count_total = await SuperadminUsuarioService.count_usuarios_globales(**filter_kwargs)
        list_result = await SuperadminUsuarioService.get_usuarios_globales(
            limit=100,
            **filter_kwargs,
        )

    assert count_total == list_result["total_usuarios"]
    assert len(build_calls) >= 2
    assert all(call == build_calls[0] for call in build_calls)
    assert all(cliente_id is None for cliente_id in kwargs_calls)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_shared_mono_tenant_uses_cliente_id_filter():
    cliente_id = HYBRID_FIXTURE_TENANT_SHARED
    captured_sql: list[str] = []

    async def _execute_query(*args, **kwargs):
        captured_sql.append(str(args[0]))
        return [{"total": 5}]

    mock_cliente = type(
        "C",
        (),
        {
            "cliente_id": cliente_id,
            "razon_social": "Shared SA",
            "subdominio": "shared",
            "codigo_cliente": "SHARED",
            "nombre_comercial": None,
        },
    )()

    with patch(
        f"{SERVICE}.ClienteService.obtener_cliente_por_id",
        new=AsyncMock(return_value=mock_cliente),
    ), patch(RESOLVE_DB_TYPE, new=AsyncMock(return_value="single")), patch(
        RESOLVE_KWARGS,
        new=AsyncMock(return_value={"connection_type": "default", "client_id": cliente_id}),
    ), patch(EXECUTE_QUERY, new=AsyncMock(side_effect=_execute_query)):
        total = await SuperadminUsuarioService.count_usuarios_globales(cliente_id=cliente_id)

    assert total == 5
    assert any("cliente_id" in sql.lower() for sql in captured_sql)
    assert len(captured_sql) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_dedicated_mono_tenant_no_cliente_id_in_where():
    cliente_id = HYBRID_FIXTURE_TENANT_DEDICATED
    captured_sql: list[str] = []

    async def _execute_query(*args, **kwargs):
        captured_sql.append(str(args[0]))
        return [{"total": 12}]

    mock_cliente = type(
        "C",
        (),
        {
            "cliente_id": cliente_id,
            "razon_social": "Dedicated SA",
            "subdominio": "acmee",
            "codigo_cliente": "ACMEE",
            "nombre_comercial": None,
        },
    )()

    resolve_kwargs = AsyncMock(
        return_value={"connection_type": "default", "client_id": cliente_id}
    )

    with patch(
        f"{SERVICE}.ClienteService.obtener_cliente_por_id",
        new=AsyncMock(return_value=mock_cliente),
    ), patch(RESOLVE_DB_TYPE, new=AsyncMock(return_value="multi")), patch(
        RESOLVE_KWARGS, new=resolve_kwargs
    ), patch(EXECUTE_QUERY, new=AsyncMock(side_effect=_execute_query)):
        total = await SuperadminUsuarioService.count_usuarios_globales(cliente_id=cliente_id)

    assert total == 12
    assert all("u.cliente_id = ?" not in sql for sql in captured_sql)
    resolve_kwargs.assert_awaited_once_with(cliente_id)
    assert len(captured_sql) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_does_not_invoke_enrichment(mock_global_list_execute):
    reachability = AsyncMock()
    obtener_roles = AsyncMock()
    get_level = AsyncMock()

    with patch(REACHABILITY, new=reachability), patch(OBTENER_ROLES, new=obtener_roles), patch(
        GET_LEVEL, new=get_level
    ):
        await SuperadminUsuarioService.count_usuarios_globales()

    reachability.assert_not_called()
    obtener_roles.assert_not_called()
    get_level.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_executes_only_count_query(mock_global_list_execute):
    queries: list[str] = []

    async def _execute_query(*args, **kwargs):
        queries.append(str(args[0]))
        if "COUNT(*)" in str(args[0]):
            return [{"total": 2}]
        return mock_global_list_execute["rows"]

    with patch(EXECUTE_QUERY, new=AsyncMock(side_effect=_execute_query)):
        await SuperadminUsuarioService.count_usuarios_globales()

    assert len(queries) == 1
    assert "COUNT(*)" in queries[0]
    assert "OFFSET" not in queries[0]
    assert "FETCH NEXT" not in queries[0]
