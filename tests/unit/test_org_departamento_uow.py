"""UoW — org_departamento queries dual-path (Ola 1)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.infrastructure.database.queries.org.departamento_queries import (
    create_departamento,
    get_departamento_by_codigo,
    get_departamento_by_id,
)

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
DEPARTAMENTO_ID = uuid4()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_departamento_by_codigo_with_session_uses_session_no_execute_query():
    session = AsyncMock()
    select_result = MagicMock()
    select_result.fetchone = MagicMock(return_value=None)
    session.execute.return_value = select_result
    with patch(
        "app.infrastructure.database.queries.org.departamento_queries.execute_query",
        new_callable=AsyncMock,
    ) as mock_execute_query:
        result = await get_departamento_by_codigo(
            CLIENT_ID, EMPRESA_ID, "DEP001", session=session
        )

    session.execute.assert_awaited_once()
    mock_execute_query.assert_not_called()
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_departamento_by_codigo_without_session_keeps_legacy_execute_query():
    with patch(
        "app.infrastructure.database.queries.org.departamento_queries.execute_query",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_execute_query:
        result = await get_departamento_by_codigo(CLIENT_ID, EMPRESA_ID, "DEP001")

    mock_execute_query.assert_awaited_once()
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_departamento_by_id_with_session_uses_session_no_execute_query():
    session = AsyncMock()
    select_result = MagicMock()
    select_result.fetchone = MagicMock(return_value=None)
    session.execute.return_value = select_result
    with patch(
        "app.infrastructure.database.queries.org.departamento_queries.execute_query",
        new_callable=AsyncMock,
    ) as mock_execute_query:
        result = await get_departamento_by_id(
            CLIENT_ID, DEPARTAMENTO_ID, EMPRESA_ID, session=session
        )

    session.execute.assert_awaited_once()
    mock_execute_query.assert_not_called()
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_departamento_with_session_uses_session_no_execute_insert():
    session = AsyncMock()
    session.execute.return_value = MagicMock()
    departamento_row = {
        "departamento_id": DEPARTAMENTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "DEP001",
        "nombre": "Ventas",
        "es_activo": True,
    }
    with patch(
        "app.infrastructure.database.queries.org.departamento_queries.get_departamento_by_id",
        new_callable=AsyncMock,
        return_value=departamento_row,
    ) as mock_get_by_id:
        with patch(
            "app.infrastructure.database.queries.org.departamento_queries.execute_insert",
            new_callable=AsyncMock,
        ) as mock_execute_insert:
            result = await create_departamento(
                CLIENT_ID,
                {
                    "departamento_id": DEPARTAMENTO_ID,
                    "empresa_id": EMPRESA_ID,
                    "codigo": "DEP001",
                    "nombre": "Ventas",
                },
                session=session,
            )

    session.execute.assert_awaited_once()
    mock_execute_insert.assert_not_called()
    mock_get_by_id.assert_awaited_once_with(
        CLIENT_ID, DEPARTAMENTO_ID, empresa_id=EMPRESA_ID, session=session
    )
    assert result == departamento_row


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_departamento_without_session_keeps_legacy_execute_insert():
    departamento_row = {
        "departamento_id": DEPARTAMENTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "DEP001",
        "nombre": "Ventas",
        "es_activo": True,
    }
    with patch(
        "app.infrastructure.database.queries.org.departamento_queries.execute_insert",
        new_callable=AsyncMock,
    ) as mock_execute_insert:
        with patch(
            "app.infrastructure.database.queries.org.departamento_queries.get_departamento_by_id",
            new_callable=AsyncMock,
            return_value=departamento_row,
        ) as mock_get_by_id:
            result = await create_departamento(
                CLIENT_ID,
                {
                    "departamento_id": DEPARTAMENTO_ID,
                    "empresa_id": EMPRESA_ID,
                    "codigo": "DEP001",
                    "nombre": "Ventas",
                },
            )

    mock_execute_insert.assert_awaited_once()
    mock_get_by_id.assert_awaited_once_with(
        CLIENT_ID, DEPARTAMENTO_ID, empresa_id=EMPRESA_ID
    )
    assert result == departamento_row
