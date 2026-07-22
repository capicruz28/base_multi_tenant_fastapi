"""Ola 1.2 — org_cargo integración con motor de códigos."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.core.tenant.routing import OPERATION_CLASS_TENANT_DATA
from app.modules.org.application.services import cargo_service
from app.modules.org.presentation.schemas import CargoCreate

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
CARGO_ID = uuid4()
MONEDA_ID = uuid4()


def _cargo_create(*, codigo: str | None = "CAR001") -> CargoCreate:
    return CargoCreate(
        empresa_id=EMPRESA_ID,
        codigo=codigo,
        nombre="Analista Senior",
        moneda_salarial=MONEDA_ID,
    )


def _cargo_row(codigo: str) -> dict:
    return {
        "cargo_id": CARGO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": codigo,
        "nombre": "Analista Senior",
        "moneda_salarial": MONEDA_ID,
        "es_activo": True,
    }


def _session_context_manager(session):
    @asynccontextmanager
    async def _cm():
        yield session

    return _cm()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_cargo_servicio_auto_generate_without_codigo():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _cargo_create(codigo=None)

    with patch(
        "app.modules.org.application.services.cargo_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.cargo_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.org.application.services.cargo_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ) as mock_get_conn:
                with patch(
                    "app.modules.org.application.services.cargo_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    return_value="CAR001",
                ) as mock_resolve:
                    with patch(
                        "app.modules.org.application.services.cargo_service.create_cargo",
                        new_callable=AsyncMock,
                        return_value=_cargo_row("CAR001"),
                    ) as mock_create:
                        result = await cargo_service.create_cargo_servicio(
                            client_id=CLIENT_ID, data=data
                        )

    mock_get_conn.assert_called_once_with(CLIENT_ID, OPERATION_CLASS_TENANT_DATA)
    session.begin.assert_called_once()
    mock_resolve.assert_awaited_once_with(
        "org_cargo",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=EMPRESA_ID,
        manual_code=None,
    )
    mock_create.assert_awaited_once()
    assert mock_create.await_args.kwargs["session"] is session
    assert mock_create.await_args.kwargs["data"]["codigo"] == "CAR001"
    assert result.codigo == "CAR001"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_cargo_servicio_manual_codigo_accepted():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _cargo_create(codigo="CAR999")

    with patch(
        "app.modules.org.application.services.cargo_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.cargo_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.org.application.services.cargo_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.org.application.services.cargo_service.get_cargo_by_codigo",
                    new_callable=AsyncMock,
                    return_value=None,
                ) as mock_dup:
                    with patch(
                        "app.modules.org.application.services.cargo_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                        new_callable=AsyncMock,
                        return_value="CAR999",
                    ) as mock_resolve:
                        with patch(
                            "app.modules.org.application.services.cargo_service.create_cargo",
                            new_callable=AsyncMock,
                            return_value=_cargo_row("CAR999"),
                        ):
                            result = await cargo_service.create_cargo_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    mock_dup.assert_awaited_once_with(
        CLIENT_ID, EMPRESA_ID, "CAR999", session=session
    )
    mock_resolve.assert_awaited_once_with(
        "org_cargo",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=EMPRESA_ID,
        manual_code="CAR999",
    )
    assert result.codigo == "CAR999"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_cargo_servicio_duplicate_manual_raises_conflict():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _cargo_create(codigo="CAR001")

    with patch(
        "app.modules.org.application.services.cargo_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.cargo_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.org.application.services.cargo_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.org.application.services.cargo_service.get_cargo_by_codigo",
                    new_callable=AsyncMock,
                    return_value=_cargo_row("CAR001"),
                ):
                    with patch(
                        "app.modules.org.application.services.cargo_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                        new_callable=AsyncMock,
                    ) as mock_resolve:
                        with pytest.raises(ConflictError):
                            await cargo_service.create_cargo_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    mock_resolve.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_cargo_servicio_cfg_missing_propagates():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _cargo_create(codigo=None)

    with patch(
        "app.modules.org.application.services.cargo_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.cargo_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.org.application.services.cargo_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.org.application.services.cargo_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    side_effect=NotFoundError(
                        detail="Configuración de secuencia no encontrada.",
                        internal_code="CFG_SEQUENCE_NOT_FOUND",
                    ),
                ):
                    with patch(
                        "app.modules.org.application.services.cargo_service.create_cargo",
                        new_callable=AsyncMock,
                    ) as mock_create:
                        with pytest.raises(NotFoundError):
                            await cargo_service.create_cargo_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    mock_create.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_cargo_servicio_single_transaction_begin():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _cargo_create(codigo=None)

    with patch(
        "app.modules.org.application.services.cargo_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.cargo_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.org.application.services.cargo_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.org.application.services.cargo_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                    return_value="CAR002",
                ):
                    with patch(
                        "app.modules.org.application.services.cargo_service.create_cargo",
                        new_callable=AsyncMock,
                        return_value=_cargo_row("CAR002"),
                    ):
                        await cargo_service.create_cargo_servicio(
                            client_id=CLIENT_ID, data=data
                        )

    session.begin.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_cargo_servicio_conflict_rolls_back_via_begin_context():
    session = AsyncMock()
    begin_cm = AsyncMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    data = _cargo_create(codigo="CAR001")

    with patch(
        "app.modules.org.application.services.cargo_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.cargo_service.ensure_empresa_in_tenant",
            new_callable=AsyncMock,
        ):
            with patch(
                "app.modules.org.application.services.cargo_service.get_connection_for_tenant",
                return_value=_session_context_manager(session),
            ):
                with patch(
                    "app.modules.org.application.services.cargo_service.get_cargo_by_codigo",
                    new_callable=AsyncMock,
                    return_value=_cargo_row("CAR001"),
                ):
                    with patch(
                        "app.modules.org.application.services.cargo_service.create_cargo",
                        new_callable=AsyncMock,
                    ) as mock_create:
                        with pytest.raises(ConflictError):
                            await cargo_service.create_cargo_servicio(
                                client_id=CLIENT_ID, data=data
                            )

    session.begin.assert_called_once()
    mock_create.assert_not_called()


@pytest.mark.unit
def test_cargo_create_schema_accepts_missing_codigo():
    data = CargoCreate(
        empresa_id=EMPRESA_ID,
        nombre="Analista",
        moneda_salarial=MONEDA_ID,
    )
    assert data.codigo is None
