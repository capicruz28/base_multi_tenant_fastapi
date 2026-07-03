"""F13-J3 — fail-soft dashboard ClienteService.obtener_estadisticas."""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.core.tenant.platform_tenant_reachability import (
    ReachabilityResult,
    ReachabilityStatus,
)
from app.core.tenant.routing import DEDICATED_ROUTE_FAIL_CLOSED
from app.infrastructure.database.connection_async import DatabaseConnection
from app.modules.tenant.application.services.cliente_service import ClienteService
from tests.integration.helpers.hybrid_mock_metadata import (
    HYBRID_FIXTURE_TENANT_DEDICATED,
    HYBRID_FIXTURE_TENANT_SHARED,
)

SERVICE = "app.modules.tenant.application.services.cliente_service"
REACHABILITY = "app.core.tenant.platform_tenant_reachability.check_platform_tenant_reachability"
RESOLVE_KWARGS = "app.core.tenant.platform_tenant_data_store.resolve_platform_tenant_data_execute_kwargs"
EXECUTE_QUERY = f"{SERVICE}.execute_query"


def _cliente_read(cliente_id, *, tipo_instalacion: str = "shared"):
    return SimpleNamespace(
        cliente_id=cliente_id,
        razon_social="Test Tenant",
        fecha_creacion=datetime(2025, 6, 1, 10, 0, 0),
        fecha_ultimo_acceso=datetime(2026, 6, 1, 8, 0, 0),
        estado_suscripcion="activo",
        plan_suscripcion="enterprise",
        tipo_instalacion=tipo_instalacion,
    )


def _reachable(cliente_id: UUID) -> ReachabilityResult:
    return ReachabilityResult(
        cliente_id=cliente_id,
        status=ReachabilityStatus.REACHABLE,
        metadata={"database_type": "single"},
    )


def _not_configured(cliente_id) -> ReachabilityResult:
    return ReachabilityResult(
        cliente_id=cliente_id,
        status=ReachabilityStatus.NOT_CONFIGURED,
        internal_code=DEDICATED_ROUTE_FAIL_CLOSED,
        message="Storage Endpoint ausente en cliente_conexion.",
    )


@pytest.fixture
def mock_cliente():
    async def _get(cliente_id):
        return _cliente_read(cliente_id, tipo_instalacion="dedicated")

    with patch.object(ClienteService, "obtener_cliente_por_id", new=AsyncMock(side_effect=_get)):
        yield


@pytest.mark.unit
@pytest.mark.asyncio
async def test_shared_reachable_flujo_completo(mock_cliente):
    cliente_id = HYBRID_FIXTURE_TENANT_SHARED
    query_results = iter(
        [
            [{"total_conexiones": 0}],
            [{"total_activos": 5, "total_inactivos": 1}],
            [{"modulos_activos": 2, "modulos_contratados": 4}],
        ]
    )

    resolve_mock = AsyncMock(return_value={"connection_type": DatabaseConnection.DEFAULT, "client_id": cliente_id})

    with patch(REACHABILITY, new=AsyncMock(return_value=_reachable(cliente_id))), patch(
        RESOLVE_KWARGS, new=resolve_mock
    ), patch(EXECUTE_QUERY, new=AsyncMock(side_effect=lambda *_a, **_k: next(query_results))):
        stats = await ClienteService.obtener_estadisticas(cliente_id)

    assert stats.total_usuarios == 5
    assert stats.total_usuarios_inactivos == 1
    assert stats.modulos_activos == 2
    assert stats.modulos_contratados == 4
    assert stats.conexiones_bd == 0
    assert stats.dias_activo >= 0
    assert stats.tenant_data_available is None
    resolve_mock.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dedicated_valid_flujo_completo(mock_cliente):
    cliente_id = HYBRID_FIXTURE_TENANT_DEDICATED
    query_results = iter(
        [
            [{"total_conexiones": 1}],
            [{"total_activos": 3, "total_inactivos": 0}],
            [{"modulos_activos": 3, "modulos_contratados": 3}],
        ]
    )

    resolve_mock = AsyncMock(
        return_value={
            "connection_type": DatabaseConnection.DEFAULT,
            "client_id": cliente_id,
            "identity_scope": "engine_scoped",
        }
    )

    with patch(REACHABILITY, new=AsyncMock(return_value=_reachable(cliente_id))), patch(
        RESOLVE_KWARGS, new=resolve_mock
    ), patch(EXECUTE_QUERY, new=AsyncMock(side_effect=lambda *_a, **_k: next(query_results))):
        stats = await ClienteService.obtener_estadisticas(cliente_id)

    assert stats.total_usuarios == 3
    assert stats.modulos_activos == 3
    assert stats.conexiones_bd == 1
    assert stats.tenant_data_available is None
    resolve_mock.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dedicated_sin_conexion_estadisticas_parciales_http200(mock_cliente):
    cliente_id = uuid4()
    conexiones_cp = [{"total_conexiones": 0}]

    resolve_mock = AsyncMock()

    with patch(REACHABILITY, new=AsyncMock(return_value=_not_configured(cliente_id))), patch(
        RESOLVE_KWARGS, new=resolve_mock
    ), patch(EXECUTE_QUERY, new=AsyncMock(return_value=conexiones_cp)) as mock_eq:
        stats = await ClienteService.obtener_estadisticas(cliente_id)

    assert stats.total_usuarios is None
    assert stats.total_usuarios_inactivos is None
    assert stats.modulos_activos is None
    assert stats.modulos_contratados is None
    assert stats.conexiones_bd == 0
    assert stats.razon_social == "Test Tenant"
    assert stats.estado_suscripcion == "activo"
    assert stats.plan_actual == "enterprise"
    assert stats.tenant_data_available is False
    assert stats.tenant_data_reachability == ReachabilityStatus.NOT_CONFIGURED.value
    assert stats.tenant_data_internal_code == DEDICATED_ROUTE_FAIL_CLOSED
    resolve_mock.assert_not_called()
    assert mock_eq.await_count == 1
    assert mock_eq.await_args.kwargs["connection_type"] == DatabaseConnection.ADMIN


@pytest.mark.unit
@pytest.mark.asyncio
async def test_degraded_serialization_incluye_metadata(mock_cliente):
    cliente_id = uuid4()

    with patch(REACHABILITY, new=AsyncMock(return_value=_not_configured(cliente_id))), patch(
        EXECUTE_QUERY, new=AsyncMock(return_value=[{"total_conexiones": 0}])
    ):
        stats = await ClienteService.obtener_estadisticas(cliente_id)

    dumped = stats.model_dump()
    assert dumped["tenant_data_available"] is False
    assert dumped["tenant_data_reachability"] == "not_configured"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reachable_serialization_sin_metadata_degradacion(mock_cliente):
    cliente_id = uuid4()
    query_results = iter(
        [
            [{"total_conexiones": 1}],
            [{"total_activos": 1, "total_inactivos": 0}],
            [{"modulos_activos": 1, "modulos_contratados": 1}],
        ]
    )

    with patch(REACHABILITY, new=AsyncMock(return_value=_reachable(cliente_id))), patch(
        RESOLVE_KWARGS, new=AsyncMock(return_value={"connection_type": DatabaseConnection.DEFAULT, "client_id": cliente_id})
    ), patch(EXECUTE_QUERY, new=AsyncMock(side_effect=lambda *_a, **_k: next(query_results))):
        stats = await ClienteService.obtener_estadisticas(cliente_id)

    dumped = stats.model_dump()
    assert "tenant_data_available" not in dumped
    assert "tenant_data_reachability" not in dumped
