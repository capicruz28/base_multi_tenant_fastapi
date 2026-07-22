"""F19 — cliente_auth_config reutiliza la AsyncSession del onboarding (sin 2ª conexión ADMIN)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.auth.auth_config_gateway import AuthConfigGateway
from app.infrastructure.database.queries.auth.auth_config_queries_core import (
    insert_config_core,
    select_config_id_by_cliente_id_core,
)

CLIENTE_ID = uuid4()
CONFIG_ID = uuid4()


def _select_result(value):
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=value)
    return result


def _insert_result(mapping):
    row = MagicMock()
    row._mapping = mapping
    result = MagicMock()
    result.first = MagicMock(return_value=row)
    return result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_insert_config_core_with_session_uses_session_no_new_connection():
    session = AsyncMock()
    session.execute.return_value = _insert_result(
        {"config_id": CONFIG_ID, "cliente_id": CLIENTE_ID}
    )
    with patch(
        "app.infrastructure.database.queries_async.execute_insert",
        new_callable=AsyncMock,
    ) as mock_execute_insert:
        result = await insert_config_core({"cliente_id": CLIENTE_ID}, session=session)

    session.execute.assert_awaited_once()
    mock_execute_insert.assert_not_called()
    assert result["config_id"] == CONFIG_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_select_config_id_with_session_uses_session_no_new_connection():
    session = AsyncMock()
    session.execute.return_value = _select_result(None)
    with patch(
        "app.infrastructure.database.queries_async.execute_query",
        new_callable=AsyncMock,
    ) as mock_execute_query:
        result = await select_config_id_by_cliente_id_core(CLIENTE_ID, session=session)

    session.execute.assert_awaited_once()
    mock_execute_query.assert_not_called()
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_insert_config_core_without_session_keeps_legacy_connection():
    with patch(
        "app.infrastructure.database.queries_async.execute_insert",
        new_callable=AsyncMock,
        return_value={"config_id": CONFIG_ID, "cliente_id": CLIENTE_ID},
    ) as mock_execute_insert:
        result = await insert_config_core({"cliente_id": CLIENTE_ID})

    mock_execute_insert.assert_awaited_once()
    assert result["config_id"] == CONFIG_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_select_config_id_without_session_keeps_legacy_connection():
    with patch(
        "app.infrastructure.database.queries_async.execute_query",
        new_callable=AsyncMock,
        return_value=[{"config_id": CONFIG_ID}],
    ) as mock_execute_query:
        result = await select_config_id_by_cliente_id_core(CLIENTE_ID)

    mock_execute_query.assert_awaited_once()
    assert result == CONFIG_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_gateway_propagates_session_to_core():
    session = AsyncMock()
    with patch(
        "app.core.auth.auth_config_gateway.select_config_id_by_cliente_id_core",
        new_callable=AsyncMock,
        return_value=None,
    ) as mock_select, patch(
        "app.core.auth.auth_config_gateway.insert_config_core",
        new_callable=AsyncMock,
        return_value={"config_id": CONFIG_ID},
    ) as mock_insert:
        exists = await AuthConfigGateway.config_exists(CLIENTE_ID, session=session)
        await AuthConfigGateway.insert_config({"cliente_id": CLIENTE_ID}, session=session)

    assert exists is False
    mock_select.assert_awaited_once_with(CLIENTE_ID, session=session)
    mock_insert.assert_awaited_once_with({"cliente_id": CLIENTE_ID}, session=session)
