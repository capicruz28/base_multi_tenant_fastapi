"""F11-P1 / F13-C2 — Dedicated menu catalog routing + TD-08 JOIN catálogo."""
from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import and_, select

from app.core.authorization.menu_catalog_store import resolve_menu_catalog_query1_target
from app.core.tenant.context import reset_tenant_context, set_tenant_context
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.query_helpers import apply_tenant_filter
from app.infrastructure.database.tables import UsuarioTable
from app.infrastructure.database.tables_modulos import (
    ClienteModuloTable,
    ModuloMenuTable,
    ModuloTable,
)
from app.modules.modulos.application.services.modulo_menu_service import ModuloMenuService
from app.modules.modulos.presentation.schemas import MenuUsuarioResponse
from tests.integration.helpers.hybrid_mock_metadata import (
    HYBRID_FIXTURE_TENANT_DEDICATED,
    HYBRID_FIXTURE_TENANT_SHARED,
    build_dedicated_metadata,
    build_shared_metadata,
    build_tenant_context,
)

CLIENT_ID = uuid4()
USER_ID = uuid4()
SHARED_CTX_ID = HYBRID_FIXTURE_TENANT_SHARED
DEDICATED_CTX_ID = HYBRID_FIXTURE_TENANT_DEDICATED
RESOLVER_MODULE = "app.core.tenant.operation_store_resolver"


@pytest.fixture
def dedicated_tenant_context():
    ctx = build_tenant_context(
        DEDICATED_CTX_ID,
        build_dedicated_metadata(DEDICATED_CTX_ID),
        subdominio="dedicated-mock",
        codigo_cliente="DEDICATED",
    )
    tokens = set_tenant_context(ctx)
    yield ctx
    reset_tenant_context(tokens)


@pytest.fixture
def shared_tenant_context():
    ctx = build_tenant_context(
        SHARED_CTX_ID,
        build_shared_metadata(SHARED_CTX_ID),
        subdominio="shared-mock",
        codigo_cliente="SHARED",
    )
    tokens = set_tenant_context(ctx)
    yield ctx
    reset_tenant_context(tokens)


def _menu_catalog_row() -> Dict[str, Any]:
    return {
        "modulo_id": uuid4(),
        "modulo_codigo": "INV",
        "modulo_nombre": "Inventario",
        "menu_id": uuid4(),
        "menu_codigo": "inv_prod",
        "menu_nombre": "Productos",
    }


def _is_query1_catalog(q: str) -> bool:
    return "modulo_menu" in q and "rol_menu_permiso" not in q


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_menu_catalog_shared_returns_default_via_resolver():
    metadata = build_shared_metadata(SHARED_CTX_ID)
    with patch(
        f"{RESOLVER_MODULE}.get_connection_metadata_async",
        new=AsyncMock(return_value=metadata),
    ):
        conn, client_id = await resolve_menu_catalog_query1_target(SHARED_CTX_ID)

    assert conn == DatabaseConnection.DEFAULT
    assert client_id == SHARED_CTX_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_menu_catalog_dedicated_returns_default():
    metadata = build_dedicated_metadata(DEDICATED_CTX_ID)
    with patch(
        f"{RESOLVER_MODULE}.get_connection_metadata_async",
        new=AsyncMock(return_value=metadata),
    ):
        conn, client_id = await resolve_menu_catalog_query1_target(DEDICATED_CTX_ID)

    assert conn == DatabaseConnection.DEFAULT
    assert client_id == DEDICATED_CTX_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_obtener_menu_usuario_shared_query1_uses_default():
    captured: Dict[str, Any] = {}
    metadata = build_shared_metadata(CLIENT_ID)

    async def fake_execute_query(query, *args, **kwargs):
        q = query if isinstance(query, str) else str(query)
        if "rol_menu_permiso" in q:
            return []
        if _is_query1_catalog(q):
            captured["connection_type"] = kwargs.get("connection_type")
            captured["client_id"] = kwargs.get("client_id")
            return [_menu_catalog_row()]
        return []

    with patch(
        f"{RESOLVER_MODULE}.get_connection_metadata_async",
        new=AsyncMock(return_value=metadata),
    ), patch(
        "app.modules.modulos.application.services.modulo_menu_service.execute_query",
        new=AsyncMock(side_effect=fake_execute_query),
    ), patch.object(
        ModuloMenuService,
        "_get_required_permissions_by_modulo",
        new=AsyncMock(return_value={}),
    ), patch(
        "app.modules.modulos.application.services.modulo_menu_service.transformar_sp_menu_usuario",
        return_value=MenuUsuarioResponse(modulos=[]),
    ):
        await ModuloMenuService.obtener_menu_usuario(
            usuario_id=USER_ID,
            cliente_id=CLIENT_ID,
        )

    assert captured["connection_type"] == DatabaseConnection.DEFAULT
    assert captured["client_id"] == CLIENT_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_obtener_menu_usuario_dedicated_query1_uses_default():
    metadata = build_dedicated_metadata(DEDICATED_CTX_ID)
    captured: Dict[str, Any] = {}

    async def fake_execute_query(query, *args, **kwargs):
        q = query if isinstance(query, str) else str(query)
        if "rol_menu_permiso" in q:
            return []
        if _is_query1_catalog(q):
            captured["connection_type"] = kwargs.get("connection_type")
            captured["client_id"] = kwargs.get("client_id")
            return [_menu_catalog_row()]
        return []

    with patch(
        f"{RESOLVER_MODULE}.get_connection_metadata_async",
        new=AsyncMock(return_value=metadata),
    ), patch(
        "app.modules.modulos.application.services.modulo_menu_service.execute_query",
        new=AsyncMock(side_effect=fake_execute_query),
    ), patch.object(
        ModuloMenuService,
        "_get_required_permissions_by_modulo",
        new=AsyncMock(return_value={}),
    ), patch(
        "app.modules.modulos.application.services.modulo_menu_service.transformar_sp_menu_usuario",
        return_value=MenuUsuarioResponse(modulos=[]),
    ):
        await ModuloMenuService.obtener_menu_usuario(
            usuario_id=USER_ID,
            cliente_id=DEDICATED_CTX_ID,
        )

    assert captured["connection_type"] == DatabaseConnection.DEFAULT
    assert captured["client_id"] == DEDICATED_CTX_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_obtener_menu_usuario_impersonation_dedicated_uses_target_metadata_not_host():
    """Platform host + target Dedicated: resolver usa metadata del target (F13-C2)."""
    platform_host_ctx = build_tenant_context(
        SHARED_CTX_ID,
        build_shared_metadata(SHARED_CTX_ID),
        subdominio="platform",
        codigo_cliente="SYSTEM",
    )
    tokens = set_tenant_context(platform_host_ctx)
    dedicated_metadata = build_dedicated_metadata(DEDICATED_CTX_ID)
    captured: Dict[str, Any] = {}

    async def fake_execute_query(query, *args, **kwargs):
        q = query if isinstance(query, str) else str(query)
        if "rol_menu_permiso" in q:
            return []
        if _is_query1_catalog(q):
            captured["connection_type"] = kwargs.get("connection_type")
            captured["client_id"] = kwargs.get("client_id")
            return [_menu_catalog_row()]
        return []

    try:
        with patch(
            f"{RESOLVER_MODULE}.get_connection_metadata_async",
            new=AsyncMock(return_value=dedicated_metadata),
        ), patch(
            "app.modules.modulos.application.services.modulo_menu_service.execute_query",
            new=AsyncMock(side_effect=fake_execute_query),
        ), patch.object(
            ModuloMenuService,
            "_get_required_permissions_by_modulo",
            new=AsyncMock(return_value={}),
        ), patch(
            "app.modules.modulos.application.services.modulo_menu_service.transformar_sp_menu_usuario",
            return_value=MenuUsuarioResponse(modulos=[]),
        ):
            await ModuloMenuService.obtener_menu_usuario(
                usuario_id=USER_ID,
                cliente_id=DEDICATED_CTX_ID,
            )
    finally:
        reset_tenant_context(tokens)

    assert captured["connection_type"] == DatabaseConnection.DEFAULT
    assert captured["client_id"] == DEDICATED_CTX_ID


@pytest.mark.unit
def test_dedicated_global_catalog_join_skips_td08(dedicated_tenant_context):
    cliente_id = dedicated_tenant_context.client_id
    query = select(ModuloMenuTable.c.menu_id).select_from(
        ModuloMenuTable.join(
            ModuloTable,
            ModuloMenuTable.c.modulo_id == ModuloTable.c.modulo_id,
        ).join(
            ClienteModuloTable,
            and_(
                ModuloTable.c.modulo_id == ClienteModuloTable.c.modulo_id,
                ClienteModuloTable.c.cliente_id == cliente_id,
            ),
        )
    )
    filtered = apply_tenant_filter(query, client_id=cliente_id)
    assert filtered is query


@pytest.mark.unit
def test_dedicated_non_global_table_still_enforces_td08(dedicated_tenant_context):
    query = select(UsuarioTable).where(UsuarioTable.c.es_activo.is_(True))
    filtered = apply_tenant_filter(query, table_name="usuario")
    where_sql = str(filtered.whereclause).lower()
    assert "cliente_id" in where_sql


@pytest.mark.unit
def test_shared_global_catalog_join_no_regression(shared_tenant_context):
    query = select(ModuloMenuTable.c.menu_id).select_from(
        ModuloMenuTable.join(
            ModuloTable,
            ModuloMenuTable.c.modulo_id == ModuloTable.c.modulo_id,
        )
    )
    filtered = apply_tenant_filter(query, client_id=shared_tenant_context.client_id)
    assert filtered is query
