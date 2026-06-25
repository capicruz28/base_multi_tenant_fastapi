"""
Hybrid Dedicated Mock Harness — pytest fixtures (PR-F0-01).

Cargado explícitamente por PRs F0-02+ vía:
    pytest_plugins = ("tests.integration.conftest_hybrid",)

Sin conexiones reales. Sin SQL Server. Sin create_async_engine.
"""
from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from app.core.tenant.context import reset_tenant_context, set_tenant_context
from app.infrastructure.database.connection_async import DatabaseConnection
from tests.integration.helpers.hybrid_mock_metadata import (
    HYBRID_FIXTURE_TENANT_DEDICATED,
    HYBRID_FIXTURE_TENANT_SHARED,
    build_dedicated_metadata,
    build_shared_metadata,
    build_tenant_context,
    resolve_engine_key,
)


@pytest.fixture
def hybrid_shared_client_id() -> UUID:
    return HYBRID_FIXTURE_TENANT_SHARED


@pytest.fixture
def hybrid_dedicated_client_id() -> UUID:
    return HYBRID_FIXTURE_TENANT_DEDICATED


@pytest.fixture
def hybrid_shared_metadata(hybrid_shared_client_id: UUID) -> Dict[str, Any]:
    return build_shared_metadata(hybrid_shared_client_id)


@pytest.fixture
def hybrid_dedicated_metadata(hybrid_dedicated_client_id: UUID) -> Dict[str, Any]:
    return build_dedicated_metadata(hybrid_dedicated_client_id)


@pytest.fixture
def mock_cp_metadata_lookup(
    hybrid_shared_client_id: UUID,
    hybrid_dedicated_client_id: UUID,
    hybrid_shared_metadata: Dict[str, Any],
    hybrid_dedicated_metadata: Dict[str, Any],
):
    """Mock CP lookup — parchea get_connection_metadata_async sin BD."""
    metadata_by_client: Dict[UUID, Dict[str, Any]] = {
        hybrid_shared_client_id: hybrid_shared_metadata,
        hybrid_dedicated_client_id: hybrid_dedicated_metadata,
    }

    async def _mock_get_connection_metadata_async(client_id: UUID) -> Dict[str, Any]:
        if client_id not in metadata_by_client:
            raise ValueError(f"No mock CP metadata registrada para client_id={client_id}")
        return metadata_by_client[client_id]

    with patch(
        "app.core.tenant.routing.get_connection_metadata_async",
        side_effect=_mock_get_connection_metadata_async,
    ):
        yield metadata_by_client


@pytest.fixture
def mock_hybrid_async_engine():
    """Mock AsyncEngine registry — parchea _get_async_engine sin create_async_engine."""
    mock_engines: Dict[str, MagicMock] = {}

    def _mock_get_async_engine(
        connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
        client_id=None,
        connection_metadata=None,
    ):
        key = resolve_engine_key(client_id, connection_type)
        if key not in mock_engines:
            mock_engines[key] = MagicMock(name=f"AsyncEngine_{key}")
        return mock_engines[key]

    with patch(
        "app.infrastructure.database.connection_async._get_async_engine",
        side_effect=_mock_get_async_engine,
    ):
        yield mock_engines


@pytest.fixture
def hybrid_shared_tenant_context(
    hybrid_shared_client_id: UUID,
    hybrid_shared_metadata: Dict[str, Any],
):
    ctx = build_tenant_context(
        hybrid_shared_client_id,
        hybrid_shared_metadata,
        subdominio="hybrid-shared-mock",
        codigo_cliente="HYBRID_SHARED",
    )
    tokens = set_tenant_context(ctx)
    yield ctx
    reset_tenant_context(tokens)


@pytest.fixture
def hybrid_dedicated_tenant_context(
    hybrid_dedicated_client_id: UUID,
    hybrid_dedicated_metadata: Dict[str, Any],
):
    ctx = build_tenant_context(
        hybrid_dedicated_client_id,
        hybrid_dedicated_metadata,
        subdominio="hybrid-dedicated-mock",
        codigo_cliente="HYBRID_DEDICATED",
    )
    tokens = set_tenant_context(ctx)
    yield ctx
    reset_tenant_context(tokens)


@pytest.fixture
def hybrid_harness(
    hybrid_shared_client_id: UUID,
    hybrid_dedicated_client_id: UUID,
    hybrid_shared_metadata: Dict[str, Any],
    hybrid_dedicated_metadata: Dict[str, Any],
    mock_cp_metadata_lookup: Dict[UUID, Dict[str, Any]],
    mock_hybrid_async_engine: Dict[str, MagicMock],
):
    """Agregador de fixtures atómicas — sin lógica adicional."""
    yield {
        "shared_client_id": hybrid_shared_client_id,
        "dedicated_client_id": hybrid_dedicated_client_id,
        "shared_metadata": hybrid_shared_metadata,
        "dedicated_metadata": hybrid_dedicated_metadata,
        "cp_metadata_map": mock_cp_metadata_lookup,
        "mock_engines": mock_hybrid_async_engine,
    }
