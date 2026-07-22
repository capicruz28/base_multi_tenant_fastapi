"""UoW — org_centro_costo queries dual-path (Ola 1)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.infrastructure.database.queries.org.centro_costo_queries import (
    create_centro_costo,
    get_centro_costo_by_codigo,
    get_centro_costo_by_id,
)

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
CENTRO_COSTO_ID = uuid4()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_centro_costo_by_codigo_with_session_uses_session_no_execute_query():
    session = AsyncMock()
    select_result = MagicMock()
    select_result.fetchone = MagicMock(return_value=None)
    session.execute.return_value = select_result
    with patch(
        "app.infrastructure.database.queries.org.centro_costo_queries.execute_query",
        new_callable=AsyncMock,
    ) as mock_execute_query:
        result = await get_centro_costo_by_codigo(
            CLIENT_ID, EMPRESA_ID, "CC001", session=session
        )

    session.execute.assert_awaited_once()
    mock_execute_query.assert_not_called()
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_centro_costo_by_codigo_without_session_keeps_legacy_execute_query():
    with patch(
        "app.infrastructure.database.queries.org.centro_costo_queries.execute_query",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_execute_query:
        result = await get_centro_costo_by_codigo(CLIENT_ID, EMPRESA_ID, "CC001")

    mock_execute_query.assert_awaited_once()
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_centro_costo_by_id_with_session_uses_session_no_execute_query():
    session = AsyncMock()
    select_result = MagicMock()
    select_result.fetchone = MagicMock(return_value=None)
    session.execute.return_value = select_result
    with patch(
        "app.infrastructure.database.queries.org.centro_costo_queries.execute_query",
        new_callable=AsyncMock,
    ) as mock_execute_query:
        result = await get_centro_costo_by_id(
            CLIENT_ID, CENTRO_COSTO_ID, EMPRESA_ID, session=session
        )

    session.execute.assert_awaited_once()
    mock_execute_query.assert_not_called()
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_centro_costo_with_session_uses_session_no_execute_insert():
    session = AsyncMock()
    session.execute.return_value = MagicMock()
    centro_costo_row = {
        "centro_costo_id": CENTRO_COSTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CC001",
        "nombre": "Administración",
        "tipo_centro_costo": "operativo",
        "es_activo": True,
    }
    with patch(
        "app.infrastructure.database.queries.org.centro_costo_queries.get_centro_costo_by_id",
        new_callable=AsyncMock,
        return_value=centro_costo_row,
    ) as mock_get_by_id:
        with patch(
            "app.infrastructure.database.queries.org.centro_costo_queries.execute_insert",
            new_callable=AsyncMock,
        ) as mock_execute_insert:
            result = await create_centro_costo(
                CLIENT_ID,
                {
                    "centro_costo_id": CENTRO_COSTO_ID,
                    "empresa_id": EMPRESA_ID,
                    "codigo": "CC001",
                    "nombre": "Administración",
                    "tipo_centro_costo": "operativo",
                },
                session=session,
            )

    session.execute.assert_awaited_once()
    mock_execute_insert.assert_not_called()
    mock_get_by_id.assert_awaited_once_with(
        CLIENT_ID, CENTRO_COSTO_ID, empresa_id=EMPRESA_ID, session=session
    )
    assert result == centro_costo_row


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_centro_costo_without_session_keeps_legacy_execute_insert():
    centro_costo_row = {
        "centro_costo_id": CENTRO_COSTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CC001",
        "nombre": "Administración",
        "tipo_centro_costo": "operativo",
        "es_activo": True,
    }
    with patch(
        "app.infrastructure.database.queries.org.centro_costo_queries.execute_insert",
        new_callable=AsyncMock,
    ) as mock_execute_insert:
        with patch(
            "app.infrastructure.database.queries.org.centro_costo_queries.get_centro_costo_by_id",
            new_callable=AsyncMock,
            return_value=centro_costo_row,
        ) as mock_get_by_id:
            result = await create_centro_costo(
                CLIENT_ID,
                {
                    "centro_costo_id": CENTRO_COSTO_ID,
                    "empresa_id": EMPRESA_ID,
                    "codigo": "CC001",
                    "nombre": "Administración",
                    "tipo_centro_costo": "operativo",
                },
            )

    mock_execute_insert.assert_awaited_once()
    mock_get_by_id.assert_awaited_once_with(
        CLIENT_ID, CENTRO_COSTO_ID, empresa_id=EMPRESA_ID
    )
    assert result == centro_costo_row
