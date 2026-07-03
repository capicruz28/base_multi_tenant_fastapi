"""F13-C4 — Platform tenant_data store wire-up unit tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from datetime import datetime, timezone

from app.core.identity.identity_scope import IdentityScope
from app.core.tenant.operation_store_types import EngineKind, OperationPlane
from app.core.tenant.platform_tenant_data_store import (
    resolve_platform_tenant_data_database_type,
    resolve_platform_tenant_data_execute_kwargs,
    resolve_platform_tenant_data_target,
)
from app.core.tenant.routing import OPERATION_CLASS_TENANT_DATA
from app.infrastructure.database.connection_async import DatabaseConnection
from tests.integration.helpers.hybrid_mock_metadata import (
    HYBRID_FIXTURE_TENANT_DEDICATED,
    HYBRID_FIXTURE_TENANT_SHARED,
    build_dedicated_metadata,
    build_shared_metadata,
)

from app.core.tenant.platform_tenant_reachability import (
    ReachabilityResult,
    ReachabilityStatus,
)
from app.modules.tenant.application.services.cliente_service import ClienteService

STORE_MODULE = "app.core.tenant.platform_tenant_data_store"
RESOLVER_MODULE = "app.core.tenant.operation_store_resolver"


@pytest.fixture
def mock_metadata():
    def _apply(metadata: dict):
        return patch(
            f"{RESOLVER_MODULE}.get_connection_metadata_async",
            new=AsyncMock(return_value=metadata),
        )

    return _apply


@pytest.mark.unit
@pytest.mark.asyncio
async def test_platform_tenant_data_shared_target(mock_metadata):
    cliente_id = HYBRID_FIXTURE_TENANT_SHARED
    with mock_metadata(build_shared_metadata(cliente_id)):
        conn, cid = await resolve_platform_tenant_data_target(cliente_id)
    assert conn == DatabaseConnection.DEFAULT
    assert cid == cliente_id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_platform_tenant_data_dedicated_target(mock_metadata):
    cliente_id = HYBRID_FIXTURE_TENANT_DEDICATED
    with mock_metadata(build_dedicated_metadata(cliente_id)):
        conn, cid = await resolve_platform_tenant_data_target(cliente_id)
    assert conn == DatabaseConnection.DEFAULT
    assert cid == cliente_id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_platform_tenant_data_execute_kwargs_dedicated_engine_scoped(mock_metadata):
    cliente_id = uuid4()
    with mock_metadata(build_dedicated_metadata(cliente_id)):
        kwargs = await resolve_platform_tenant_data_execute_kwargs(cliente_id)
    assert kwargs["connection_type"] == DatabaseConnection.DEFAULT
    assert kwargs["client_id"] == cliente_id
    assert kwargs["identity_scope"] == IdentityScope.ENGINE_SCOPED
    assert kwargs["operation_class"] == OPERATION_CLASS_TENANT_DATA


@pytest.mark.unit
@pytest.mark.asyncio
async def test_platform_tenant_data_database_type_from_target_not_host(mock_metadata):
    """Platform host shared + target dedicated → multi (F13-C4 impersonation/dashboard)."""
    dedicated_id = uuid4()
    with mock_metadata(build_dedicated_metadata(dedicated_id)):
        database_type = await resolve_platform_tenant_data_database_type(dedicated_id)
    assert database_type == "multi"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_obtener_estadisticas_uses_tenant_data_store(mock_metadata):
    from datetime import datetime
    from types import SimpleNamespace

    cliente_id = uuid4()
    cliente_read = SimpleNamespace(
        cliente_id=cliente_id,
        razon_social="Test",
        fecha_creacion=datetime.now(),
        fecha_ultimo_acceso=None,
        estado_suscripcion="activo",
        plan_suscripcion="trial",
        tipo_instalacion="dedicated",
    )

    query_results = iter(
        [
            [{"total_conexiones": 1}],
            [{"total_activos": 2, "total_inactivos": 0}],
            [{"modulos_activos": 3, "modulos_contratados": 3}],
        ]
    )

    async def fake_execute_query(*args, **kwargs):
        return next(query_results)

    with (
        mock_metadata(build_dedicated_metadata(cliente_id)),
        patch.object(
            ClienteService,
            "obtener_cliente_por_id",
            new=AsyncMock(return_value=cliente_read),
        ),
        patch(
            "app.core.tenant.platform_tenant_reachability.check_platform_tenant_reachability",
            new=AsyncMock(
                return_value=ReachabilityResult(
                    cliente_id=cliente_id,
                    status=ReachabilityStatus.REACHABLE,
                    metadata={"database_type": "multi"},
                )
            ),
        ),
        patch(
            "app.modules.tenant.application.services.cliente_service.execute_query",
            new=AsyncMock(side_effect=fake_execute_query),
        ) as mock_eq,
    ):
        stats = await ClienteService.obtener_estadisticas(cliente_id)

    assert stats.total_usuarios == 2
    assert stats.modulos_activos == 3
    usuario_call = mock_eq.await_args_list[1]
    assert usuario_call.kwargs["connection_type"] == DatabaseConnection.DEFAULT
    assert usuario_call.kwargs["client_id"] == cliente_id
