"""PR-F1-07 — Fallback shared observability (RD-08 amended)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.core.tenant.cache import (
    connection_cache,
    get_metadata_fallback_shared_total,
    reset_metadata_fallback_shared_total,
)
from app.core.tenant.routing import (
    _resolve_connection_metadata_uncached,
    clear_intra_request_route_cache,
)

CLIENT_ID = UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")


@pytest.fixture(autouse=True)
def _reset_observability_state():
    clear_intra_request_route_cache()
    connection_cache.invalidate(CLIENT_ID)
    reset_metadata_fallback_shared_total()
    yield
    clear_intra_request_route_cache()
    connection_cache.invalidate(CLIENT_ID)
    reset_metadata_fallback_shared_total()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_shared_fallback_increments_metadata_fallback_shared_total():
    assert get_metadata_fallback_shared_total() == 0

    with patch(
        "app.core.tenant.routing._query_connection_metadata_from_db_async",
        AsyncMock(return_value=None),
    ), patch(
        "app.infrastructure.database.connection_async.get_db_connection",
        side_effect=RuntimeError("simulated control plane failure"),
    ):
        metadata = await _resolve_connection_metadata_uncached(CLIENT_ID)

    assert metadata["database_type"] == "single"
    assert metadata["tipo_instalacion"] == "shared"
    assert get_metadata_fallback_shared_total() == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_shared_fallback_logs_rd08_warning(caplog):
    with patch(
        "app.core.tenant.routing._query_connection_metadata_from_db_async",
        AsyncMock(return_value=None),
    ), patch(
        "app.infrastructure.database.connection_async.get_db_connection",
        side_effect=RuntimeError("simulated control plane failure"),
    ):
        await _resolve_connection_metadata_uncached(CLIENT_ID)

    assert any(
        "fallback (RD-08)" in record.message
        for record in caplog.records
        if record.levelname == "WARNING"
    )
