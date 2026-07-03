"""F13-J1 — platform_tenant_reachability unit tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import DatabaseError
from app.core.tenant.platform_tenant_reachability import (
    ReachabilityStatus,
    check_platform_tenant_reachability,
)
from app.core.tenant.routing import DEDICATED_ROUTE_FAIL_CLOSED
from tests.integration.helpers.hybrid_mock_metadata import (
    HYBRID_FIXTURE_TENANT_DEDICATED,
    HYBRID_FIXTURE_TENANT_SHARED,
    build_dedicated_metadata,
    build_shared_metadata,
)

ROUTING = "app.core.tenant.platform_tenant_reachability.get_connection_metadata_async"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_shared_reachable():
    with patch(ROUTING, new=AsyncMock(return_value=build_shared_metadata(HYBRID_FIXTURE_TENANT_SHARED))):
        result = await check_platform_tenant_reachability(HYBRID_FIXTURE_TENANT_SHARED)
    assert result.status == ReachabilityStatus.REACHABLE
    assert result.metadata is not None
    assert result.metadata.get("database_type") == "single"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dedicated_valid_reachable():
    with patch(ROUTING, new=AsyncMock(return_value=build_dedicated_metadata(HYBRID_FIXTURE_TENANT_DEDICATED))):
        result = await check_platform_tenant_reachability(HYBRID_FIXTURE_TENANT_DEDICATED)
    assert result.status == ReachabilityStatus.REACHABLE
    assert result.metadata is not None
    assert result.metadata.get("database_type") == "multi"
    assert result.metadata.get("servidor")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dedicated_sin_cliente_conexion_not_configured():
    cliente_id = uuid4()
    with patch(
        ROUTING,
        new=AsyncMock(
            side_effect=DatabaseError(
                detail=(
                    f"Tenant {cliente_id} dedicated (RI-39): "
                    "Storage Endpoint ausente o credenciales inválidas en cliente_conexion."
                ),
                internal_code=DEDICATED_ROUTE_FAIL_CLOSED,
            )
        ),
    ):
        result = await check_platform_tenant_reachability(cliente_id)
    assert result.status == ReachabilityStatus.NOT_CONFIGURED
    assert result.internal_code == DEDICATED_ROUTE_FAIL_CLOSED
    assert result.metadata is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_metadata_inconsistente():
    cliente_id = uuid4()
    with patch(
        ROUTING,
        new=AsyncMock(
            side_effect=DatabaseError(
                detail=(
                    f"Tenant {cliente_id} con Installation Mode dedicated no puede enrutar "
                    "con database_type='single' (RI-39)."
                ),
                internal_code=DEDICATED_ROUTE_FAIL_CLOSED,
            )
        ),
    ):
        result = await check_platform_tenant_reachability(cliente_id)
    assert result.status == ReachabilityStatus.METADATA_INCOMPLETE
    assert result.metadata is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_unexpected_error_does_not_swallow_non_metadata_database_error():
    with patch(
        ROUTING,
        new=AsyncMock(
            side_effect=DatabaseError(
                detail="Error en la consulta",
                internal_code="DB_QUERY_ERROR",
            )
        ),
    ):
        with pytest.raises(DatabaseError) as exc_info:
            await check_platform_tenant_reachability(uuid4())
    assert exc_info.value.internal_code == "DB_QUERY_ERROR"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_unexpected_error_status_for_non_database_exception():
    with patch(ROUTING, new=AsyncMock(side_effect=RuntimeError("cache corrupt"))):
        result = await check_platform_tenant_reachability(uuid4())
    assert result.status == ReachabilityStatus.UNEXPECTED_ERROR
    assert "cache corrupt" in (result.message or "")
