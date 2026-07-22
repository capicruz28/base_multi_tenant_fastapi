"""F2A — inv_movimiento integración Motor (AUTO_REQUIRED) + BR-IMM."""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.inv.application.services import movimiento_service
from app.modules.inv.presentation.schemas import MovimientoCreate, MovimientoUpdate

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
MOVIMIENTO_ID = uuid4()
TIPO_MOVIMIENTO_ID = uuid4()
MONEDA_ID = uuid4()
USUARIO_ID = uuid4()


def _mov_create() -> MovimientoCreate:
    return MovimientoCreate(
        empresa_id=EMPRESA_ID,
        tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
        fecha_contable=date(2026, 6, 12),
    )


def _mov_row(numero: str = "MOV000001") -> dict:
    return {
        "movimiento_id": MOVIMIENTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_movimiento": numero,
        "tipo_movimiento_id": TIPO_MOVIMIENTO_ID,
        "fecha_movimiento": date(2026, 6, 12),
        "fecha_contable": date(2026, 6, 12),
        "estado": "borrador",
        "moneda_id": MONEDA_ID,
        "usuario_creacion_id": USUARIO_ID,
    }


def _fake_uow(session):
    uow = AsyncMock()
    uow.session = session
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_movimiento_servicio_allocates_inv_movimiento():
    session = AsyncMock()
    uow = _fake_uow(session)
    data = _mov_create()

    with patch(
        "app.modules.inv.application.services.movimiento_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ), patch(
        "app.modules.inv.application.services.movimiento_service.ensure_empresa_in_tenant",
        new_callable=AsyncMock,
    ), patch(
        "app.modules.inv.application.services.movimiento_service._validate_movimiento_cabecera_refs",
        new_callable=AsyncMock,
    ), patch(
        "app.modules.inv.application.services.movimiento_service._resolve_moneda_id",
        new_callable=AsyncMock,
        return_value=MONEDA_ID,
    ), patch(
        "app.modules.inv.application.services.movimiento_service.unit_of_work",
        return_value=uow,
    ), patch(
        "app.modules.inv.application.services.movimiento_service.InvCodigoGenerationService.resolve_codigo_for_create",
        new_callable=AsyncMock,
        return_value="MOV000001",
    ) as mock_resolve, patch(
        "app.modules.inv.application.services.movimiento_service.create_movimiento",
        new_callable=AsyncMock,
        return_value=_mov_row(),
    ) as mock_create:
        result = await movimiento_service.create_movimiento_servicio(
            client_id=CLIENT_ID,
            data=data,
            usuario_id=USUARIO_ID,
        )

    mock_resolve.assert_awaited_once_with(
        "inv_movimiento",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=EMPRESA_ID,
        manual_code=None,
    )
    assert mock_create.await_args.kwargs["session"] is session
    assert mock_create.await_args.kwargs["data"]["numero_movimiento"] == "MOV000001"
    assert result.numero_movimiento == "MOV000001"


@pytest.mark.unit
def test_movimiento_create_schema_excludes_numero_movimiento():
    assert "numero_movimiento" not in MovimientoCreate.model_fields
    data = MovimientoCreate(
        empresa_id=EMPRESA_ID,
        tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
        fecha_contable=date(2026, 6, 12),
    )
    assert "numero_movimiento" not in data.model_dump()


@pytest.mark.unit
def test_movimiento_update_schema_excludes_numero_movimiento():
    assert "numero_movimiento" not in MovimientoUpdate.model_fields
    upd = MovimientoUpdate.model_validate(
        {"observaciones": "x", "numero_movimiento": "MOV999"}
    )
    assert "numero_movimiento" not in upd.model_dump(exclude_unset=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_movimiento_servicio_does_not_call_motor():
    row = _mov_row()
    updated = {**row, "observaciones": "editado"}
    data = MovimientoUpdate(observaciones="editado")

    with patch(
        "app.modules.inv.application.services.movimiento_service.require_session_empresa_id",
        return_value=EMPRESA_ID,
    ), patch(
        "app.modules.inv.application.services.movimiento_service.get_movimiento_by_id",
        new_callable=AsyncMock,
        return_value=row,
    ), patch(
        "app.modules.inv.application.services.movimiento_service._validate_movimiento_cabecera_refs",
        new_callable=AsyncMock,
    ), patch(
        "app.modules.inv.application.services.movimiento_service.update_movimiento",
        new_callable=AsyncMock,
        return_value=updated,
    ) as mock_upd, patch(
        "app.modules.inv.application.services.movimiento_service.InvCodigoGenerationService.resolve_codigo_for_create",
        new_callable=AsyncMock,
    ) as mock_motor:
        result = await movimiento_service.update_movimiento_servicio(
            client_id=CLIENT_ID,
            movimiento_id=MOVIMIENTO_ID,
            data=data,
        )

    payload = mock_upd.await_args.kwargs["data"]
    assert "numero_movimiento" not in payload
    mock_motor.assert_not_awaited()
    assert result.numero_movimiento == "MOV000001"
