"""UoW — org_cargo queries dual-path (Ola 1.2)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.infrastructure.database.queries.org.cargo_queries import (
    create_cargo,
    get_cargo_by_codigo,
    get_cargo_by_id,
)

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
CARGO_ID = uuid4()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_cargo_by_codigo_with_session_uses_session_no_execute_query():
    session = AsyncMock()
    select_result = MagicMock()
    select_result.fetchone = MagicMock(return_value=None)
    session.execute.return_value = select_result
    with patch(
        "app.infrastructure.database.queries.org.cargo_queries.execute_query",
        new_callable=AsyncMock,
    ) as mock_execute_query:
        result = await get_cargo_by_codigo(
            CLIENT_ID, EMPRESA_ID, "CAR001", session=session
        )

    session.execute.assert_awaited_once()
    mock_execute_query.assert_not_called()
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_cargo_by_codigo_without_session_keeps_legacy_execute_query():
    with patch(
        "app.infrastructure.database.queries.org.cargo_queries.execute_query",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_execute_query:
        result = await get_cargo_by_codigo(CLIENT_ID, EMPRESA_ID, "CAR001")

    mock_execute_query.assert_awaited_once()
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_cargo_by_id_with_session_uses_session_no_execute_query():
    session = AsyncMock()
    select_result = MagicMock()
    select_result.fetchone = MagicMock(return_value=None)
    session.execute.return_value = select_result
    with patch(
        "app.infrastructure.database.queries.org.cargo_queries.execute_query",
        new_callable=AsyncMock,
    ) as mock_execute_query:
        result = await get_cargo_by_id(
            CLIENT_ID, CARGO_ID, EMPRESA_ID, session=session
        )

    session.execute.assert_awaited_once()
    mock_execute_query.assert_not_called()
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_cargo_with_session_uses_session_no_execute_insert():
    session = AsyncMock()
    session.execute.return_value = MagicMock()
    cargo_row = {
        "cargo_id": CARGO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CAR001",
        "nombre": "Analista",
        "moneda_salarial": uuid4(),
        "es_activo": True,
    }
    with patch(
        "app.infrastructure.database.queries.org.cargo_queries.get_cargo_by_id",
        new_callable=AsyncMock,
        return_value=cargo_row,
    ) as mock_get_by_id:
        with patch(
            "app.infrastructure.database.queries.org.cargo_queries.execute_insert",
            new_callable=AsyncMock,
        ) as mock_execute_insert:
            result = await create_cargo(
                CLIENT_ID,
                {
                    "cargo_id": CARGO_ID,
                    "empresa_id": EMPRESA_ID,
                    "codigo": "CAR001",
                    "nombre": "Analista",
                    "moneda_salarial": cargo_row["moneda_salarial"],
                },
                session=session,
            )

    session.execute.assert_awaited_once()
    mock_execute_insert.assert_not_called()
    mock_get_by_id.assert_awaited_once_with(
        CLIENT_ID, CARGO_ID, empresa_id=EMPRESA_ID, session=session
    )
    assert result == cargo_row


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_cargo_without_session_keeps_legacy_execute_insert():
    cargo_row = {
        "cargo_id": CARGO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CAR001",
        "nombre": "Analista",
        "moneda_salarial": uuid4(),
        "es_activo": True,
    }
    with patch(
        "app.infrastructure.database.queries.org.cargo_queries.execute_insert",
        new_callable=AsyncMock,
    ) as mock_execute_insert:
        with patch(
            "app.infrastructure.database.queries.org.cargo_queries.get_cargo_by_id",
            new_callable=AsyncMock,
            return_value=cargo_row,
        ) as mock_get_by_id:
            result = await create_cargo(
                CLIENT_ID,
                {
                    "cargo_id": CARGO_ID,
                    "empresa_id": EMPRESA_ID,
                    "codigo": "CAR001",
                    "nombre": "Analista",
                    "moneda_salarial": cargo_row["moneda_salarial"],
                },
            )

    mock_execute_insert.assert_awaited_once()
    mock_get_by_id.assert_awaited_once_with(
        CLIENT_ID, CARGO_ID, empresa_id=EMPRESA_ID
    )
    assert result == cargo_row
