"""PR-F1-04 — Fail-closed dedicated routing (RD-08 / RI-39)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.core.exceptions import DatabaseError
from app.core.tenant.cache import connection_cache
from app.core.tenant.routing import (
    DEDICATED_ROUTE_FAIL_CLOSED,
    _validate_dedicated_route_metadata,
    clear_intra_request_route_cache,
    get_connection_metadata_async,
)
from app.infrastructure.database.connection_async import (
    DatabaseConnection,
    _build_async_connection_string,
)
from tests.integration.helpers.hybrid_mock_metadata import (
    build_dedicated_metadata,
    build_shared_metadata,
)

CLIENT_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")


@pytest.fixture(autouse=True)
def _reset_caches():
    clear_intra_request_route_cache()
    connection_cache.invalidate(CLIENT_ID)
    yield
    clear_intra_request_route_cache()
    connection_cache.invalidate(CLIENT_ID)


@pytest.mark.unit
def test_validate_dedicated_rejects_single_database_type():
    metadata = build_dedicated_metadata(CLIENT_ID)
    metadata["database_type"] = "single"

    with pytest.raises(DatabaseError) as exc:
        _validate_dedicated_route_metadata(metadata, CLIENT_ID)

    assert exc.value.internal_code == DEDICATED_ROUTE_FAIL_CLOSED


@pytest.mark.unit
def test_validate_dedicated_rejects_incomplete_storage_endpoint():
    metadata = build_dedicated_metadata(CLIENT_ID)
    metadata["password"] = ""

    with pytest.raises(DatabaseError) as exc:
        _validate_dedicated_route_metadata(metadata, CLIENT_ID)

    assert exc.value.internal_code == DEDICATED_ROUTE_FAIL_CLOSED


@pytest.mark.unit
def test_validate_shared_single_metadata_allowed_rd08():
    metadata = build_shared_metadata(CLIENT_ID)
    _validate_dedicated_route_metadata(metadata, CLIENT_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_l_b_cache_hit_with_stale_shared_shape_raises_for_dedicated():
    stale = build_shared_metadata(CLIENT_ID)
    stale["tipo_instalacion"] = "dedicated"
    connection_cache.set(CLIENT_ID, stale)

    with pytest.raises(DatabaseError) as exc:
        await get_connection_metadata_async(CLIENT_ID)

    assert exc.value.internal_code == DEDICATED_ROUTE_FAIL_CLOSED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_shared_missing_metadata_fallback_rd08():
    shared_fallback = build_shared_metadata(CLIENT_ID)
    with patch(
        "app.core.tenant.routing._resolve_connection_metadata_uncached",
        AsyncMock(return_value=shared_fallback),
    ):
        metadata = await get_connection_metadata_async(CLIENT_ID)

    assert metadata["database_type"] == "single"
    assert metadata["tipo_instalacion"] == "shared"


@pytest.mark.unit
def test_connection_async_rejects_dedicated_incomplete_metadata():
    metadata = build_dedicated_metadata(CLIENT_ID)
    metadata["servidor"] = None

    with pytest.raises(DatabaseError) as exc:
        _build_async_connection_string(
            DatabaseConnection.DEFAULT,
            client_id=CLIENT_ID,
            connection_metadata=metadata,
        )

    assert exc.value.internal_code == DEDICATED_ROUTE_FAIL_CLOSED


@pytest.mark.unit
def test_connection_async_accepts_valid_dedicated_metadata():
    metadata = build_dedicated_metadata(CLIENT_ID)
    conn_str = _build_async_connection_string(
        DatabaseConnection.DEFAULT,
        client_id=CLIENT_ID,
        connection_metadata=metadata,
    )
    assert "mssql+aioodbc://" in conn_str
    assert metadata["nombre_bd"] in conn_str
