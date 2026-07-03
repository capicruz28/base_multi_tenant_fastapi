"""F13-J2 — fail-soft enriquecimiento global SuperadminUsuarioService."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.core.exceptions import DatabaseError
from app.core.tenant.platform_tenant_reachability import (
    ReachabilityResult,
    ReachabilityStatus,
)
from app.core.tenant.routing import DEDICATED_ROUTE_FAIL_CLOSED
from app.modules.superadmin.application.services.superadmin_usuario_service import (
    SuperadminUsuarioService,
)
from app.modules.superadmin.presentation.schemas import ClienteInfo, RolInfo
from tests.integration.helpers.hybrid_mock_metadata import (
    HYBRID_FIXTURE_TENANT_DEDICATED,
    HYBRID_FIXTURE_TENANT_SHARED,
)

SERVICE = "app.modules.superadmin.application.services.superadmin_usuario_service"
REACHABILITY = f"{SERVICE}.check_platform_tenant_reachability"
EXECUTE_QUERY = f"{SERVICE}.execute_query"
RESOLVE_KWARGS = f"{SERVICE}.resolve_platform_tenant_data_execute_kwargs"
RESOLVE_DB_TYPE = f"{SERVICE}.resolve_platform_tenant_data_database_type"
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


def _reachable(cliente_id: UUID) -> ReachabilityResult:
    return ReachabilityResult(
        cliente_id=cliente_id,
        status=ReachabilityStatus.REACHABLE,
        metadata={"database_type": "single"},
    )


def _not_configured(cliente_id: UUID) -> ReachabilityResult:
    return ReachabilityResult(
        cliente_id=cliente_id,
        status=ReachabilityStatus.NOT_CONFIGURED,
        internal_code=DEDICATED_ROUTE_FAIL_CLOSED,
        message="Storage Endpoint ausente en cliente_conexion.",
    )


@pytest.fixture
def mock_execute_query_global():
    shared_user = uuid4()
    dedicated_user = uuid4()
    broken_tenant = uuid4()

    rows = [
        _usuario_row(shared_user, HYBRID_FIXTURE_TENANT_SHARED),
        _usuario_row(dedicated_user, HYBRID_FIXTURE_TENANT_DEDICATED),
        _usuario_row(uuid4(), broken_tenant),
    ]

    async def _execute_query(*_args, **_kwargs):
        sql = str(_args[0]) if _args else ""
        if "COUNT(*)" in sql:
            return [{"total": len(rows)}]
        return rows

    with patch(EXECUTE_QUERY, new=AsyncMock(side_effect=_execute_query)):
        yield {
            "shared_user": shared_user,
            "dedicated_user": dedicated_user,
            "broken_tenant": broken_tenant,
            "rows": rows,
        }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_global_shared_reachable_sin_campos_degradacion(mock_execute_query_global):
    async def _reachability(cliente_id: UUID, **_kwargs):
        return _reachable(cliente_id)

    roles = [RolInfo(rol_id=uuid4(), nombre="ADMIN", codigo_rol="ADMIN", nivel_acceso=3)]
    level = {"access_level": 3, "is_super_admin": False, "user_type": "admin"}

    with patch(REACHABILITY, new=AsyncMock(side_effect=_reachability)), patch(
        FETCH_CLIENTE,
        new=AsyncMock(
            side_effect=lambda cid: _cliente_info(
                cid,
                "shared" if cid == HYBRID_FIXTURE_TENANT_SHARED else "broken",
            )
        ),
    ), patch(OBTENER_ROLES, new=AsyncMock(return_value=roles)), patch(
        GET_LEVEL, new=AsyncMock(return_value=level)
    ):
        result = await SuperadminUsuarioService.get_usuarios_globales()

    shared = next(
        u for u in result["usuarios"] if u["cliente_id"] == HYBRID_FIXTURE_TENANT_SHARED
    )
    assert shared["roles"] == [r.model_dump() for r in roles]
    assert shared["access_level"] == 3
    assert "enrichment_degraded" not in shared
    assert "tenant_data_reachability" not in shared


@pytest.mark.unit
@pytest.mark.asyncio
async def test_global_dedicated_valid_sin_campos_degradacion(mock_execute_query_global):
    async def _reachability(cliente_id: UUID, **_kwargs):
        return _reachable(cliente_id)

    roles = [RolInfo(rol_id=uuid4(), nombre="ADMIN_TENANT", codigo_rol="ADMIN_TENANT", nivel_acceso=4)]
    level = {"access_level": 4, "is_super_admin": False, "user_type": "admin"}

    with patch(REACHABILITY, new=AsyncMock(side_effect=_reachability)), patch(
        FETCH_CLIENTE,
        new=AsyncMock(side_effect=lambda cid: _cliente_info(cid, "acmee")),
    ), patch(OBTENER_ROLES, new=AsyncMock(return_value=roles)), patch(
        GET_LEVEL, new=AsyncMock(return_value=level)
    ):
        result = await SuperadminUsuarioService.get_usuarios_globales()

    dedicated = next(
        u for u in result["usuarios"] if u["cliente_id"] == HYBRID_FIXTURE_TENANT_DEDICATED
    )
    assert dedicated["roles"] == [r.model_dump() for r in roles]
    assert dedicated["access_level"] == 4
    assert "enrichment_degraded" not in dedicated


@pytest.mark.unit
@pytest.mark.asyncio
async def test_global_dedicated_sin_conexion_degradado_no_aborta(mock_execute_query_global):
    broken_tenant = mock_execute_query_global["broken_tenant"]

    async def _reachability(cliente_id: UUID, **_kwargs):
        if cliente_id == broken_tenant:
            return _not_configured(cliente_id)
        return _reachable(cliente_id)

    roles_ok = [RolInfo(rol_id=uuid4(), nombre="ADMIN", codigo_rol="ADMIN", nivel_acceso=3)]
    level_ok = {"access_level": 3, "is_super_admin": False, "user_type": "admin"}
    obtener_roles = AsyncMock(return_value=roles_ok)
    get_level = AsyncMock(return_value=level_ok)

    with patch(REACHABILITY, new=AsyncMock(side_effect=_reachability)), patch(
        FETCH_CLIENTE,
        new=AsyncMock(side_effect=lambda cid: _cliente_info(cid, "innovas")),
    ), patch(OBTENER_ROLES, new=obtener_roles), patch(GET_LEVEL, new=get_level):
        result = await SuperadminUsuarioService.get_usuarios_globales()

    assert result["total_usuarios"] == 3
    assert len(result["usuarios"]) == 3

    broken = next(u for u in result["usuarios"] if u["cliente_id"] == broken_tenant)
    assert broken["roles"] == []
    assert broken["access_level"] is None
    assert broken["enrichment_degraded"] is True
    assert broken["tenant_data_available"] is False
    assert broken["tenant_data_reachability"] == ReachabilityStatus.NOT_CONFIGURED.value
    assert broken["tenant_data_internal_code"] == DEDICATED_ROUTE_FAIL_CLOSED

    reachable_calls = [
        u["cliente_id"]
        for u in result["usuarios"]
        if not u.get("enrichment_degraded")
    ]
    assert len(reachable_calls) == 2
    assert obtener_roles.await_count == 2
    assert get_level.await_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mono_tenant_no_usa_fail_soft_enrichment():
    cliente_id = HYBRID_FIXTURE_TENANT_DEDICATED
    usuario_id = uuid4()
    row = _usuario_row(usuario_id, cliente_id)

    reachability_mock = AsyncMock(return_value=_reachable(cliente_id))

    with patch(
        f"{SERVICE}.ClienteService.obtener_cliente_por_id",
        new=AsyncMock(return_value=type("C", (), {"cliente_id": cliente_id, "razon_social": "A", "subdominio": "a", "codigo_cliente": "A", "nombre_comercial": None})()),
    ), patch(RESOLVE_DB_TYPE, new=AsyncMock(return_value="multi")), patch(
        RESOLVE_KWARGS, new=AsyncMock(return_value={"connection_type": "default", "client_id": cliente_id})
    ), patch(EXECUTE_QUERY, new=AsyncMock(side_effect=lambda *_a, **_k: [{"total": 1}] if "COUNT" in str(_a[0]) else [row])), patch(
        REACHABILITY, new=reachability_mock
    ), patch(
        OBTENER_ROLES,
        new=AsyncMock(return_value=[]),
    ), patch(
        GET_LEVEL,
        new=AsyncMock(return_value={"access_level": 2, "is_super_admin": False, "user_type": "user"}),
    ):
        await SuperadminUsuarioService.get_usuarios_globales(cliente_id=cliente_id)

    reachability_mock.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mono_tenant_unreachable_sigue_fail_closed():
    cliente_id = uuid4()

    with patch(
        f"{SERVICE}.ClienteService.obtener_cliente_por_id",
        new=AsyncMock(return_value=type("C", (), {"cliente_id": cliente_id, "razon_social": "X", "subdominio": "x", "codigo_cliente": "X", "nombre_comercial": None})()),
    ), patch(
        RESOLVE_DB_TYPE,
        new=AsyncMock(
            side_effect=DatabaseError(
                detail="Storage Endpoint ausente",
                internal_code=DEDICATED_ROUTE_FAIL_CLOSED,
            )
        ),
    ):
        with pytest.raises(DatabaseError) as exc_info:
            await SuperadminUsuarioService.get_usuarios_globales(cliente_id=cliente_id)

    assert exc_info.value.internal_code == DEDICATED_ROUTE_FAIL_CLOSED
