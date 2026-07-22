"""UoW-1 — org_empresa create path: dual-path queries + session.begin() en servicio."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError
from app.infrastructure.database.queries.org.empresa_queries import (
    create_empresa,
    get_empresa_by_codigo,
)
from app.modules.org.application.services import empresa_service
from app.modules.org.presentation.schemas import EmpresaCreate

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_empresa_by_codigo_with_session_uses_session_no_execute_query():
    session = AsyncMock()
    select_result = MagicMock()
    select_result.fetchone = MagicMock(return_value=None)
    session.execute.return_value = select_result
    with patch(
        "app.infrastructure.database.queries.org.empresa_queries.execute_query",
        new_callable=AsyncMock,
    ) as mock_execute_query:
        result = await get_empresa_by_codigo(
            CLIENT_ID, "EMP002", session=session
        )

    session.execute.assert_awaited_once()
    mock_execute_query.assert_not_called()
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_empresa_by_codigo_without_session_keeps_legacy_execute_query():
    with patch(
        "app.infrastructure.database.queries.org.empresa_queries.execute_query",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_execute_query:
        result = await get_empresa_by_codigo(CLIENT_ID, "EMP002")

    mock_execute_query.assert_awaited_once()
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_empresa_with_session_uses_session_no_execute_insert():
    session = AsyncMock()
    session.execute.return_value = MagicMock()
    empresa_row = {
        "empresa_id": EMPRESA_ID,
        "cliente_id": CLIENT_ID,
        "codigo_empresa": "EMP002",
        "razon_social": "ACME SA",
        "ruc": "20123456789",
        "es_activo": True,
    }
    with patch(
        "app.infrastructure.database.queries.org.empresa_queries.get_empresa_by_id",
        new_callable=AsyncMock,
        return_value=empresa_row,
    ) as mock_get_by_id:
        with patch(
            "app.infrastructure.database.queries.org.empresa_queries.execute_insert",
            new_callable=AsyncMock,
        ) as mock_execute_insert:
            result = await create_empresa(
                CLIENT_ID,
                {
                    "empresa_id": EMPRESA_ID,
                    "codigo_empresa": "EMP002",
                    "razon_social": "ACME SA",
                    "ruc": "20123456789",
                },
                session=session,
            )

    session.execute.assert_awaited_once()
    mock_execute_insert.assert_not_called()
    mock_get_by_id.assert_awaited_once_with(
        CLIENT_ID, EMPRESA_ID, session=session
    )
    assert result == empresa_row


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_empresa_without_session_keeps_legacy_execute_insert():
    empresa_row = {
        "empresa_id": EMPRESA_ID,
        "cliente_id": CLIENT_ID,
        "codigo_empresa": "EMP002",
        "razon_social": "ACME SA",
        "ruc": "20123456789",
        "es_activo": True,
    }
    with patch(
        "app.infrastructure.database.queries.org.empresa_queries.execute_insert",
        new_callable=AsyncMock,
    ) as mock_execute_insert:
        with patch(
            "app.infrastructure.database.queries.org.empresa_queries.get_empresa_by_id",
            new_callable=AsyncMock,
            return_value=empresa_row,
        ) as mock_get_by_id:
            result = await create_empresa(
                CLIENT_ID,
                {
                    "empresa_id": EMPRESA_ID,
                    "codigo_empresa": "EMP002",
                    "razon_social": "ACME SA",
                    "ruc": "20123456789",
                },
            )

    mock_execute_insert.assert_awaited_once()
    mock_get_by_id.assert_awaited_once_with(CLIENT_ID, EMPRESA_ID)
    assert result == empresa_row


def _session_context_manager(session):
    @asynccontextmanager
    async def _cm():
        yield session

    return _cm()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_empresa_servicio_uses_single_session_and_begin():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)

    empresa_row = {
        "empresa_id": EMPRESA_ID,
        "cliente_id": CLIENT_ID,
        "codigo_empresa": "EMP002",
        "razon_social": "ACME SA",
        "nombre_comercial": "ACME",
        "ruc": "20123456789",
        "es_activo": True,
    }
    data = EmpresaCreate(
        codigo_empresa="EMP002",
        razon_social="ACME SA",
        nombre_comercial="ACME",
        ruc="20123456789",
    )

    with patch(
        "app.modules.org.application.services.empresa_service.get_connection_for_tenant",
        return_value=_session_context_manager(session),
    ) as mock_get_conn:
        with patch(
            "app.modules.org.application.services.empresa_service.get_empresa_by_codigo",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_by_codigo:
            with patch(
                "app.modules.org.application.services.empresa_service.get_empresa_by_ruc",
                new_callable=AsyncMock,
                return_value=None,
            ) as mock_by_ruc:
                with patch(
                    "app.modules.org.application.services.empresa_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    return_value="EMP002",
                ) as mock_resolve:
                    with patch(
                        "app.modules.org.application.services.empresa_service.create_empresa",
                        new_callable=AsyncMock,
                        return_value=empresa_row,
                    ) as mock_create:
                        with patch(
                            "app.modules.org.application.services.empresa_service.EmpresaBootstrapService.insertar_secuencias_codigo",
                            new_callable=AsyncMock,
                        ) as mock_bootstrap:
                            result = await empresa_service.create_empresa_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    mock_get_conn.assert_called_once()
    session.begin.assert_called_once()
    mock_by_codigo.assert_awaited_once_with(
        CLIENT_ID, "EMP002", session=session
    )
    mock_by_ruc.assert_awaited_once_with(CLIENT_ID, "20123456789", session=session)
    mock_resolve.assert_awaited_once_with(
        "org_empresa",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=None,
        manual_code="EMP002",
    )
    create_payload = mock_create.await_args.kwargs["data"]
    assert create_payload["codigo_empresa"] == "EMP002"
    mock_create.assert_awaited_once_with(
        client_id=CLIENT_ID,
        data=create_payload,
        session=session,
    )
    mock_bootstrap.assert_awaited_once_with(session, CLIENT_ID, EMPRESA_ID)
    assert result.empresa_id == EMPRESA_ID
    assert result.codigo_empresa == "EMP002"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_empresa_servicio_conflict_rolls_back_via_begin_context():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)

    data = EmpresaCreate(
        codigo_empresa="EMP002",
        razon_social="ACME SA",
        nombre_comercial="ACME",
        ruc="20123456789",
    )

    with patch(
        "app.modules.org.application.services.empresa_service.get_connection_for_tenant",
        return_value=_session_context_manager(session),
    ):
        with patch(
            "app.modules.org.application.services.empresa_service.get_empresa_by_codigo",
            new_callable=AsyncMock,
            return_value={"empresa_id": uuid4()},
        ):
            with patch(
                "app.modules.org.application.services.empresa_service.create_empresa",
                new_callable=AsyncMock,
            ) as mock_create:
                with pytest.raises(ConflictError):
                    await empresa_service.create_empresa_servicio(
                        client_id=CLIENT_ID, data=data
                    )

    session.begin.assert_called_once()
    mock_create.assert_not_called()
