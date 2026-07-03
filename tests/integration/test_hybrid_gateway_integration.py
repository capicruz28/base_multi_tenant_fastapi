"""
PR-F1-08 — Hybrid gateway integration tests (F1-WP08 / G-F1).

Ejercita infra productiva post-F1 (routing, connection_async, queries_async)
con harness mock F0-01. Sin BD real, sin create_async_engine.

DOD-F1-05: dedicated mock → engine/metadata multi; shared mock sin regresión.
RD-06 / RI-36 / RI-37 / TD-01.
"""
from __future__ import annotations

from typing import Any, Dict, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from sqlalchemy import select

from app.core.exceptions import DatabaseError
from app.core.tenant.cache import connection_cache
from app.core.tenant.routing import (
    DEDICATED_ROUTE_FAIL_CLOSED,
    clear_intra_request_route_cache,
    get_connection_for_tenant,
    get_connection_metadata_async,
)
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.tables import UsuarioTable
from tests.integration.helpers.hybrid_mock_metadata import (
    build_shared_metadata,
    resolve_engine_key,
)

pytest_plugins = ("tests.integration.conftest_hybrid",)


def _mock_async_session_cm() -> Tuple[MagicMock, AsyncMock]:
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_result.keys.return_value = ["usuario_id"]
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    return mock_cm, mock_session


@pytest.fixture(autouse=True)
def _reset_gateway_caches(
    hybrid_shared_client_id: UUID,
    hybrid_dedicated_client_id: UUID,
):
    clear_intra_request_route_cache()
    connection_cache.invalidate(hybrid_shared_client_id)
    connection_cache.invalidate(hybrid_dedicated_client_id)
    yield
    clear_intra_request_route_cache()
    connection_cache.invalidate(hybrid_shared_client_id)
    connection_cache.invalidate(hybrid_dedicated_client_id)


def _seed_l_b_cache(client_id: UUID, metadata: Dict[str, Any]) -> None:
    connection_cache.set(client_id, metadata.copy())


@pytest.mark.integration
@pytest.mark.asyncio
class TestHybridGatewayDedicatedRouting:
    """G-F1 / DOD-F1-05 — dedicated mock enruta vía prod routing (RI-36)."""

    async def test_get_connection_for_tenant_passes_multi_metadata(
        self,
        hybrid_dedicated_client_id: UUID,
        hybrid_dedicated_metadata: Dict[str, Any],
    ) -> None:
        _seed_l_b_cache(hybrid_dedicated_client_id, hybrid_dedicated_metadata)
        mock_cm, _ = _mock_async_session_cm()

        with patch(
            "app.infrastructure.database.connection_async.get_db_connection",
            return_value=mock_cm,
        ) as mock_conn:
            async with get_connection_for_tenant(cliente_id=hybrid_dedicated_client_id):
                pass

        mock_conn.assert_called_once()
        call_kwargs = mock_conn.call_args.kwargs
        assert call_kwargs["connection_metadata"]["database_type"] == "multi"
        assert (
            call_kwargs["connection_metadata"]["nombre_bd"]
            == hybrid_dedicated_metadata["nombre_bd"]
        )

    async def test_dedicated_resolves_distinct_engine_key(
        self,
        hybrid_shared_client_id: UUID,
        hybrid_dedicated_client_id: UUID,
        hybrid_shared_metadata: Dict[str, Any],
        hybrid_dedicated_metadata: Dict[str, Any],
        mock_hybrid_async_engine,
    ) -> None:
        from app.infrastructure.database import connection_async

        shared_key = resolve_engine_key(
            hybrid_shared_client_id,
            DatabaseConnection.DEFAULT,
        )
        dedicated_key = resolve_engine_key(
            hybrid_dedicated_client_id,
            DatabaseConnection.DEFAULT,
        )
        assert shared_key != dedicated_key

        shared_engine = connection_async._get_async_engine(
            DatabaseConnection.DEFAULT,
            client_id=hybrid_shared_client_id,
            connection_metadata=hybrid_shared_metadata,
        )
        dedicated_engine = connection_async._get_async_engine(
            DatabaseConnection.DEFAULT,
            client_id=hybrid_dedicated_client_id,
            connection_metadata=hybrid_dedicated_metadata,
        )
        assert shared_engine is not dedicated_engine
        assert mock_hybrid_async_engine[shared_key] is shared_engine
        assert mock_hybrid_async_engine[dedicated_key] is dedicated_engine


@pytest.mark.integration
@pytest.mark.asyncio
class TestHybridGatewaySharedRouting:
    """G-F1 / RI-37 — shared mock conserva path Single-DB observable."""

    async def test_get_connection_for_tenant_shared_single_db_path(
        self,
        hybrid_shared_client_id: UUID,
        hybrid_shared_metadata: Dict[str, Any],
    ) -> None:
        _seed_l_b_cache(hybrid_shared_client_id, hybrid_shared_metadata)
        mock_cm, _ = _mock_async_session_cm()

        with patch(
            "app.infrastructure.database.connection_async.get_db_connection",
            return_value=mock_cm,
        ) as mock_conn:
            async with get_connection_for_tenant(cliente_id=hybrid_shared_client_id):
                pass

        mock_conn.assert_called_once()
        call_kwargs = mock_conn.call_args.kwargs
        assert call_kwargs.get("connection_metadata") is None
        assert mock_conn.call_args.args[0] == DatabaseConnection.DEFAULT

    async def test_execute_query_shared_returns_list_contract(
        self,
        hybrid_shared_client_id: UUID,
        hybrid_shared_metadata: Dict[str, Any],
        hybrid_shared_tenant_context,
    ) -> None:
        _seed_l_b_cache(hybrid_shared_client_id, hybrid_shared_metadata)
        mock_cm, _ = _mock_async_session_cm()

        with patch(
            "app.infrastructure.database.connection_async.get_db_connection",
            return_value=mock_cm,
        ):
            results = await execute_query(
                select(UsuarioTable).where(UsuarioTable.c.es_activo.is_(True)),
                client_id=hybrid_shared_client_id,
            )

        assert isinstance(results, list)


@pytest.mark.integration
@pytest.mark.asyncio
class TestHybridGatewayPipelineRd06:
    """RD-06 — execute_* usa pipeline gateway unificado post-F1."""

    async def test_two_execute_queries_one_metadata_resolution(
        self,
        hybrid_shared_client_id: UUID,
        hybrid_shared_metadata: Dict[str, Any],
    ) -> None:
        from app.core.tenant.routing import _resolve_connection_metadata_uncached

        _seed_l_b_cache(hybrid_shared_client_id, hybrid_shared_metadata)
        resolve_spy = AsyncMock(wraps=_resolve_connection_metadata_uncached)
        mock_cm, _ = _mock_async_session_cm()
        query = select(UsuarioTable).where(UsuarioTable.c.es_activo.is_(True))

        with patch(
            "app.core.tenant.routing._resolve_connection_metadata_uncached",
            resolve_spy,
        ), patch(
            "app.infrastructure.database.connection_async.get_db_connection",
            return_value=mock_cm,
        ):
            await execute_query(query, client_id=hybrid_shared_client_id)
            await execute_query(query, client_id=hybrid_shared_client_id)

        assert resolve_spy.await_count == 1

    async def test_dedicated_execute_query_applies_defensive_tenant_filter(
        self,
        hybrid_dedicated_client_id: UUID,
        hybrid_dedicated_metadata: Dict[str, Any],
        hybrid_dedicated_tenant_context,
    ) -> None:
        _seed_l_b_cache(hybrid_dedicated_client_id, hybrid_dedicated_metadata)
        mock_cm, mock_session = _mock_async_session_cm()
        query = select(UsuarioTable).where(UsuarioTable.c.es_activo.is_(True))

        with patch(
            "app.infrastructure.database.connection_async.get_db_connection",
            return_value=mock_cm,
        ):
            await execute_query(query, client_id=hybrid_dedicated_client_id)

        executed_query = mock_session.execute.await_args.args[0]
        assert executed_query.whereclause is not None


@pytest.mark.integration
@pytest.mark.asyncio
class TestHybridGatewayDedicatedFailClosed:
    """DOD-F1-06 — prod routing fail-closed dedicated (F1-WP04), no fallback shared."""

    async def test_stale_dedicated_shaped_cache_raises_fail_closed(
        self,
        hybrid_dedicated_client_id: UUID,
    ) -> None:
        stale = build_shared_metadata(hybrid_dedicated_client_id)
        stale["tipo_instalacion"] = "dedicated"
        _seed_l_b_cache(hybrid_dedicated_client_id, stale)

        with pytest.raises(DatabaseError) as exc_info:
            await get_connection_metadata_async(hybrid_dedicated_client_id)

        assert exc_info.value.internal_code == DEDICATED_ROUTE_FAIL_CLOSED
