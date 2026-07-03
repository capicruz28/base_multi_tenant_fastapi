"""F11-P3 / F13-C3 — Dedicated permission catalog routing (Query B/C)."""
from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.core.authorization.permission_catalog_store import resolve_permission_catalog_target
from app.core.authorization.permission_resolver import PermissionResolverService
from app.core.tenant.context import reset_tenant_context, set_tenant_context
from app.infrastructure.database.connection_async import DatabaseConnection
from app.modules.rbac.application.services.permisos_usuario_service import (
    obtener_codigos_permiso_usuario,
)
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
PERMISO_ID = uuid4()
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
def mock_metadata():
    def _apply(metadata: dict[str, Any]):
        return patch(
            f"{RESOLVER_MODULE}.get_connection_metadata_async",
            new=AsyncMock(return_value=metadata),
        )

    return _apply


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_permission_catalog_shared_returns_default_via_resolver(mock_metadata):
    metadata = build_shared_metadata(SHARED_CTX_ID)
    with mock_metadata(metadata):
        conn, client_id = await resolve_permission_catalog_target(SHARED_CTX_ID)

    assert conn == DatabaseConnection.DEFAULT
    assert client_id == SHARED_CTX_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_permission_catalog_dedicated_returns_default(mock_metadata):
    metadata = build_dedicated_metadata(DEDICATED_CTX_ID)
    with mock_metadata(metadata):
        conn, client_id = await resolve_permission_catalog_target(DEDICATED_CTX_ID)

    assert conn == DatabaseConnection.DEFAULT
    assert client_id == DEDICATED_CTX_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_permission_catalog_platform_host_target_dedicated_uses_target_metadata(
    mock_metadata,
):
    """Platform Host + target Dedicated → metadata del target (F13-C3)."""
    platform_host_ctx = build_tenant_context(
        SHARED_CTX_ID,
        build_shared_metadata(SHARED_CTX_ID),
        subdominio="platform",
        codigo_cliente="SYSTEM",
    )
    tokens = set_tenant_context(platform_host_ctx)
    dedicated_metadata = build_dedicated_metadata(DEDICATED_CTX_ID)

    try:
        with mock_metadata(dedicated_metadata):
            conn, client_id = await resolve_permission_catalog_target(DEDICATED_CTX_ID)
    finally:
        reset_tenant_context(tokens)

    assert conn == DatabaseConnection.DEFAULT
    assert client_id == DEDICATED_CTX_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_permisos_dedicated_query_b_uses_default_catalog_store(mock_metadata):
    metadata = build_dedicated_metadata(DEDICATED_CTX_ID)
    captured: List[Dict[str, Any]] = []

    async def fake_execute_query(query, *args, **kwargs):
        q = query if isinstance(query, str) else str(query)
        if "rol_permiso" in q and "permiso_id" in q:
            return [{"permiso_id": PERMISO_ID}]
        if "FROM permiso" in q or " permiso " in q:
            captured.append(
                {
                    "connection_type": kwargs.get("connection_type"),
                    "client_id": kwargs.get("client_id"),
                }
            )
            return [{"codigo": "org.cargo.leer"}]
        return []

    with mock_metadata(metadata), patch(
        "app.modules.rbac.application.services.permisos_usuario_service.execute_query",
        new=AsyncMock(side_effect=fake_execute_query),
    ):
        codes = await obtener_codigos_permiso_usuario(
            usuario_id=USER_ID,
            cliente_id=DEDICATED_CTX_ID,
            database_type="multi",
        )

    assert codes == ["org.cargo.leer"]
    assert len(captured) == 1
    assert captured[0]["connection_type"] == DatabaseConnection.DEFAULT
    assert captured[0]["client_id"] == DEDICATED_CTX_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_permisos_single_query_unchanged_shared():
    captured: List[Dict[str, Any]] = []

    async def fake_execute_query(query, *args, **kwargs):
        q = query if isinstance(query, str) else str(query)
        if "usuario_rol" in q and "permiso" in q:
            captured.append(
                {
                    "connection_type": kwargs.get("connection_type"),
                    "client_id": kwargs.get("client_id"),
                }
            )
            return [{"codigo": "org.cargo.leer"}]
        return []

    with patch(
        "app.modules.rbac.application.services.permisos_usuario_service.execute_query",
        new=AsyncMock(side_effect=fake_execute_query),
    ):
        codes = await obtener_codigos_permiso_usuario(
            usuario_id=USER_ID,
            cliente_id=CLIENT_ID,
            database_type="single",
        )

    assert codes == ["org.cargo.leer"]
    assert len(captured) == 1
    assert captured[0]["connection_type"] == DatabaseConnection.DEFAULT
    assert captured[0]["client_id"] == CLIENT_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_module_codes_dedicated_uses_default(mock_metadata):
    metadata = build_dedicated_metadata(DEDICATED_CTX_ID)
    captured: Dict[str, Any] = {}

    async def fake_execute_query(query, *args, **kwargs):
        captured["connection_type"] = kwargs.get("connection_type")
        captured["client_id"] = kwargs.get("client_id")
        return [{"codigo": "ORG"}]

    with mock_metadata(metadata), patch(
        "app.infrastructure.database.queries_async.execute_query",
        new=AsyncMock(side_effect=fake_execute_query),
    ):
        codes = await PermissionResolverService().get_active_module_codes(DEDICATED_CTX_ID)

    assert codes == ["org"]
    assert captured["connection_type"] == DatabaseConnection.DEFAULT
    assert captured["client_id"] == DEDICATED_CTX_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_module_codes_shared_uses_default(mock_metadata):
    metadata = build_shared_metadata(SHARED_CTX_ID)
    captured: Dict[str, Any] = {}

    async def fake_execute_query(query, *args, **kwargs):
        captured["connection_type"] = kwargs.get("connection_type")
        captured["client_id"] = kwargs.get("client_id")
        return [{"codigo": "ORG"}]

    with mock_metadata(metadata), patch(
        "app.infrastructure.database.queries_async.execute_query",
        new=AsyncMock(side_effect=fake_execute_query),
    ):
        codes = await PermissionResolverService().get_active_module_codes(SHARED_CTX_ID)

    assert codes == ["org"]
    assert captured["connection_type"] == DatabaseConnection.DEFAULT
    assert captured["client_id"] == SHARED_CTX_ID
