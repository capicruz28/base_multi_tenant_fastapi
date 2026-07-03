"""PR-F1-03 — Intra-request route cache L-A (TD-01)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.core.tenant.cache import connection_cache
from app.core.tenant.routing import (
    OPERATION_CLASS_TENANT_DATA,
    clear_intra_request_route_cache,
    get_cached_route_binding,
    get_connection_for_tenant,
    get_connection_metadata_async,
    set_cached_route_binding,
)


CLIENT_ID = UUID("11111111-1111-4111-8111-111111111111")
SAMPLE_METADATA = {
    "database_type": "single",
    "nombre_bd": "bd_test",
    "tipo_instalacion": "shared",
}


@pytest.fixture(autouse=True)
def _reset_route_and_l_b_cache():
    clear_intra_request_route_cache()
    connection_cache.invalidate(CLIENT_ID)
    yield
    clear_intra_request_route_cache()
    connection_cache.invalidate(CLIENT_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_route_cache_la_hit_skips_second_metadata_resolution():
    db_mock = AsyncMock(return_value=SAMPLE_METADATA.copy())
    with patch(
        "app.core.tenant.routing._query_connection_metadata_from_db_async",
        db_mock,
    ):
        first = await get_connection_metadata_async(
            CLIENT_ID, OPERATION_CLASS_TENANT_DATA
        )
        second = await get_connection_metadata_async(
            CLIENT_ID, OPERATION_CLASS_TENANT_DATA
        )

    assert first == SAMPLE_METADATA
    assert second == SAMPLE_METADATA
    assert db_mock.await_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_two_get_connection_for_tenant_one_metadata_resolution():
    resolve_mock = AsyncMock(return_value=SAMPLE_METADATA.copy())
    mock_session = AsyncMock()
    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "app.core.tenant.routing._resolve_connection_metadata_uncached",
        resolve_mock,
    ), patch(
        "app.infrastructure.database.connection_async.get_db_connection",
        return_value=mock_cm,
    ):
        async with get_connection_for_tenant(cliente_id=CLIENT_ID):
            pass
        async with get_connection_for_tenant(cliente_id=CLIENT_ID):
            pass

    assert resolve_mock.await_count == 1


@pytest.mark.unit
def test_route_cache_key_isolated_by_operation_class():
    tenant_meta = {"database_type": "single", "nombre_bd": "shared_db"}
    set_cached_route_binding(CLIENT_ID, OPERATION_CLASS_TENANT_DATA, tenant_meta)

    assert get_cached_route_binding(CLIENT_ID, OPERATION_CLASS_TENANT_DATA) == tenant_meta
    assert get_cached_route_binding(CLIENT_ID, "control_plane") is None


@pytest.mark.unit
def test_clear_intra_request_route_cache_removes_bindings():
    set_cached_route_binding(CLIENT_ID, OPERATION_CLASS_TENANT_DATA, SAMPLE_METADATA)
    clear_intra_request_route_cache()
    assert get_cached_route_binding(CLIENT_ID, OPERATION_CLASS_TENANT_DATA) is None
