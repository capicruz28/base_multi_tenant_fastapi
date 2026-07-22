"""Fase A — inv_almacen integración con motor de códigos."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.core.tenant.routing import OPERATION_CLASS_TENANT_DATA
from app.modules.inv.application.services import almacen_service
from app.modules.inv.presentation.schemas import AlmacenCreate

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
ALMACEN_ID = uuid4()
USUARIO_ID = uuid4()


def _alm_create(*, codigo: str | None = "ALM001") -> AlmacenCreate:
    return AlmacenCreate(
        empresa_id=EMPRESA_ID,
        codigo=codigo,
        nombre="Almacen central",
        tipo_almacen="general",
    )


def _alm_row(codigo: str) -> dict:
    return {
        "almacen_id": ALMACEN_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": codigo,
        "nombre": "Almacen central",
        "tipo_almacen": "GENERAL",
        "es_activo": True,
        "usuario_creacion_id": USUARIO_ID,
    }


def _session_context_manager(session):
    @asynccontextmanager
    async def _cm():
        yield session

    return _cm()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_almacen_servicio_auto_generate_without_codigo():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _alm_create(codigo=None)

    with patch(
        "app.modules.inv.application.services.almacen_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.almacen_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.inv.application.services.almacen_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ) as mock_get_conn:
                with patch(
                    "app.modules.inv.application.services.almacen_service.InvCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    return_value="ALM001",
                ) as mock_resolve:
                    with patch(
                        "app.modules.inv.application.services.almacen_service.create_almacen",
                        new_callable=AsyncMock,
                        return_value=_alm_row("ALM001"),
                    ) as mock_create:
                        result = await almacen_service.create_almacen_servicio(
                            client_id=CLIENT_ID,
                            data=data,
                            usuario_id=USUARIO_ID,
                        )

    mock_get_conn.assert_called_once_with(CLIENT_ID, OPERATION_CLASS_TENANT_DATA)
    session.begin.assert_called_once()
    mock_resolve.assert_awaited_once_with(
        "inv_almacen",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=EMPRESA_ID,
        manual_code=None,
    )
    mock_create.assert_awaited_once()
    assert mock_create.await_args.kwargs["session"] is session
    assert mock_create.await_args.kwargs["data"]["codigo"] == "ALM001"
    assert mock_create.await_args.kwargs["data"]["usuario_creacion_id"] == USUARIO_ID
    assert result.codigo == "ALM001"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_almacen_servicio_manual_codigo_accepted():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _alm_create(codigo="ALM999")

    with patch(
        "app.modules.inv.application.services.almacen_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.almacen_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.inv.application.services.almacen_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.inv.application.services.almacen_service.get_almacen_by_codigo",
                    new_callable=AsyncMock,
                    return_value=None,
                ) as mock_dup:
                    with patch(
                        "app.modules.inv.application.services.almacen_service.InvCodigoGenerationService.resolve_codigo_for_create",
                        new_callable=AsyncMock,
                        return_value="ALM999",
                    ) as mock_resolve:
                        with patch(
                            "app.modules.inv.application.services.almacen_service.create_almacen",
                            new_callable=AsyncMock,
                            return_value=_alm_row("ALM999"),
                        ):
                            result = await almacen_service.create_almacen_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    mock_dup.assert_awaited_once_with(
        CLIENT_ID, EMPRESA_ID, "ALM999", session=session
    )
    mock_resolve.assert_awaited_once_with(
        "inv_almacen",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=EMPRESA_ID,
        manual_code="ALM999",
    )
    assert result.codigo == "ALM999"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_almacen_servicio_duplicate_manual_raises_conflict():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _alm_create(codigo="ALM001")

    with patch(
        "app.modules.inv.application.services.almacen_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.almacen_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.inv.application.services.almacen_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.inv.application.services.almacen_service.get_almacen_by_codigo",
                    new_callable=AsyncMock,
                    return_value=_alm_row("ALM001"),
                ):
                    with patch(
                        "app.modules.inv.application.services.almacen_service.InvCodigoGenerationService.resolve_codigo_for_create",
                        new_callable=AsyncMock,
                    ) as mock_resolve:
                        with pytest.raises(ConflictError):
                            await almacen_service.create_almacen_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    mock_resolve.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_almacen_servicio_cfg_missing_propagates():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _alm_create(codigo=None)

    with patch(
        "app.modules.inv.application.services.almacen_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.almacen_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.inv.application.services.almacen_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.inv.application.services.almacen_service.InvCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    side_effect=NotFoundError(
                        detail="Configuración de secuencia no encontrada.",
                        internal_code="CFG_SEQUENCE_NOT_FOUND",
                    ),
                ):
                    with patch(
                        "app.modules.inv.application.services.almacen_service.create_almacen",
                        new_callable=AsyncMock,
                    ) as mock_create:
                        with pytest.raises(NotFoundError):
                            await almacen_service.create_almacen_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    mock_create.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_almacen_servicio_single_transaction_begin():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _alm_create(codigo=None)

    with patch(
        "app.modules.inv.application.services.almacen_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.almacen_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.inv.application.services.almacen_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.inv.application.services.almacen_service.InvCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    return_value="ALM002",
                ):
                    with patch(
                        "app.modules.inv.application.services.almacen_service.create_almacen",
                        new_callable=AsyncMock,
                        return_value=_alm_row("ALM002"),
                    ):
                        await almacen_service.create_almacen_servicio(
                            client_id=CLIENT_ID, data=data
                        )

    session.begin.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_almacen_servicio_conflict_rolls_back_via_begin_context():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _alm_create(codigo="ALM001")

    with patch(
        "app.modules.inv.application.services.almacen_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.almacen_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.inv.application.services.almacen_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.inv.application.services.almacen_service.get_almacen_by_codigo",
                    new_callable=AsyncMock,
                    return_value=_alm_row("ALM001"),
                ):
                    with patch(
                        "app.modules.inv.application.services.almacen_service.create_almacen",
                        new_callable=AsyncMock,
                    ) as mock_create:
                        with pytest.raises(ConflictError):
                            await almacen_service.create_almacen_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    session.begin.assert_called_once()
    mock_create.assert_not_called()


@pytest.mark.unit
def test_almacen_create_schema_accepts_missing_codigo():
    data = AlmacenCreate(
        empresa_id=EMPRESA_ID,
        nombre="Almacen central",
        tipo_almacen="general",
    )
    assert data.codigo is None
