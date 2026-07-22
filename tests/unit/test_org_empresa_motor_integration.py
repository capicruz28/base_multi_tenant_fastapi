"""Ola 1 — org_empresa integración con motor de códigos (scope TENANT)."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.core.tenant.routing import OPERATION_CLASS_TENANT_DATA
from app.modules.org.application.services import empresa_service
from app.modules.org.presentation.schemas import EmpresaCreate

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()


def _empresa_create(*, codigo_empresa: str | None = "EMP002") -> EmpresaCreate:
    return EmpresaCreate(
        codigo_empresa=codigo_empresa,
        razon_social="ACME SA",
        nombre_comercial="ACME",
        ruc="20123456789",
    )


def _empresa_row(codigo_empresa: str) -> dict:
    return {
        "empresa_id": EMPRESA_ID,
        "cliente_id": CLIENT_ID,
        "codigo_empresa": codigo_empresa,
        "razon_social": "ACME SA",
        "nombre_comercial": "ACME",
        "ruc": "20123456789",
        "es_activo": True,
    }


def _session_context_manager(session):
    @asynccontextmanager
    async def _cm():
        yield session

    return _cm()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_empresa_servicio_auto_generate_without_codigo():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _empresa_create(codigo_empresa=None)

    with patch(
        "app.modules.org.application.services.empresa_service.get_connection_for_tenant",
        return_value=_session_context_manager(session),
    ) as mock_get_conn:
        with patch(
            "app.modules.org.application.services.empresa_service.get_empresa_by_ruc",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch(
                "app.modules.org.application.services.empresa_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                new_callable=AsyncMock,
                return_value="EMP002",
            ) as mock_resolve:
                with patch(
                    "app.modules.org.application.services.empresa_service.create_empresa",
                    new_callable=AsyncMock,
                    return_value=_empresa_row("EMP002"),
                ) as mock_create:
                    with patch(
                        "app.modules.org.application.services.empresa_service.EmpresaBootstrapService.insertar_secuencias_codigo",
                        new_callable=AsyncMock,
                    ) as mock_bootstrap:
                        result = await empresa_service.create_empresa_servicio(
                            client_id=CLIENT_ID, data=data
                        )

    mock_get_conn.assert_called_once_with(CLIENT_ID, OPERATION_CLASS_TENANT_DATA)
    session.begin.assert_called_once()
    mock_resolve.assert_awaited_once_with(
        "org_empresa",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=None,
        manual_code=None,
    )
    mock_create.assert_awaited_once()
    assert mock_create.await_args.kwargs["session"] is session
    assert mock_create.await_args.kwargs["data"]["codigo_empresa"] == "EMP002"
    mock_bootstrap.assert_awaited_once_with(session, CLIENT_ID, EMPRESA_ID)
    assert result.codigo_empresa == "EMP002"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_empresa_servicio_manual_codigo_accepted():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _empresa_create(codigo_empresa="EMP999")

    with patch(
        "app.modules.org.application.services.empresa_service.get_connection_for_tenant",
        return_value=_session_context_manager(session),
    ):
        with patch(
            "app.modules.org.application.services.empresa_service.get_empresa_by_codigo",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_dup:
            with patch(
                "app.modules.org.application.services.empresa_service.get_empresa_by_ruc",
                new_callable=AsyncMock,
                return_value=None,
            ):
                with patch(
                    "app.modules.org.application.services.empresa_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    return_value="EMP999",
                ) as mock_resolve:
                    with patch(
                        "app.modules.org.application.services.empresa_service.create_empresa",
                        new_callable=AsyncMock,
                        return_value=_empresa_row("EMP999"),
                    ):
                        with patch(
                            "app.modules.org.application.services.empresa_service.EmpresaBootstrapService.insertar_secuencias_codigo",
                            new_callable=AsyncMock,
                        ):
                            result = await empresa_service.create_empresa_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    mock_dup.assert_awaited_once_with(CLIENT_ID, "EMP999", session=session)
    mock_resolve.assert_awaited_once_with(
        "org_empresa",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=None,
        manual_code="EMP999",
    )
    assert result.codigo_empresa == "EMP999"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_empresa_servicio_duplicate_manual_raises_conflict():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _empresa_create(codigo_empresa="EMP002")

    with patch(
        "app.modules.org.application.services.empresa_service.get_connection_for_tenant",
        return_value=_session_context_manager(session),
    ):
        with patch(
            "app.modules.org.application.services.empresa_service.get_empresa_by_codigo",
            new_callable=AsyncMock,
            return_value=_empresa_row("EMP002"),
        ):
            with patch(
                "app.modules.org.application.services.empresa_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                new_callable=AsyncMock,
            ) as mock_resolve:
                with patch(
                    "app.modules.org.application.services.empresa_service.create_empresa",
                    new_callable=AsyncMock,
                ) as mock_create:
                    with pytest.raises(ConflictError):
                        await empresa_service.create_empresa_servicio(
                            client_id=CLIENT_ID, data=data
                        )

    mock_resolve.assert_not_awaited()
    mock_create.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_empresa_servicio_cfg_missing_propagates():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _empresa_create(codigo_empresa=None)

    with patch(
        "app.modules.org.application.services.empresa_service.get_connection_for_tenant",
        return_value=_session_context_manager(session),
    ):
        with patch(
            "app.modules.org.application.services.empresa_service.get_empresa_by_ruc",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch(
                "app.modules.org.application.services.empresa_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                new_callable=AsyncMock,
                side_effect=NotFoundError(
                    detail="Configuración de secuencia no encontrada.",
                    internal_code="CFG_SEQUENCE_NOT_FOUND",
                ),
            ):
                with patch(
                    "app.modules.org.application.services.empresa_service.create_empresa",
                    new_callable=AsyncMock,
                ) as mock_create:
                    with pytest.raises(NotFoundError):
                        await empresa_service.create_empresa_servicio(
                            client_id=CLIENT_ID, data=data
                        )

    mock_create.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_empresa_servicio_single_transaction_begin():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _empresa_create(codigo_empresa=None)

    with patch(
        "app.modules.org.application.services.empresa_service.get_connection_for_tenant",
        return_value=_session_context_manager(session),
    ):
        with patch(
            "app.modules.org.application.services.empresa_service.get_empresa_by_ruc",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch(
                "app.modules.org.application.services.empresa_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                new_callable=AsyncMock,
                return_value="EMP002",
            ):
                with patch(
                    "app.modules.org.application.services.empresa_service.create_empresa",
                    new_callable=AsyncMock,
                    return_value=_empresa_row("EMP002"),
                ):
                    with patch(
                        "app.modules.org.application.services.empresa_service.EmpresaBootstrapService.insertar_secuencias_codigo",
                        new_callable=AsyncMock,
                    ):
                        await empresa_service.create_empresa_servicio(
                            client_id=CLIENT_ID, data=data
                        )

    session.begin.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_empresa_servicio_conflict_rolls_back_via_begin_context():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _empresa_create(codigo_empresa="EMP002")

    with patch(
        "app.modules.org.application.services.empresa_service.get_connection_for_tenant",
        return_value=_session_context_manager(session),
    ):
        with patch(
            "app.modules.org.application.services.empresa_service.get_empresa_by_codigo",
            new_callable=AsyncMock,
            return_value=_empresa_row("EMP002"),
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


@pytest.mark.unit
def test_empresa_create_schema_accepts_missing_codigo_empresa():
    data = EmpresaCreate(
        razon_social="ACME SA",
        ruc="20123456789",
    )
    assert data.codigo_empresa is None
