"""F2A — inv_inventario_fisico integración Motor (AUTO_REQUIRED) + BR-IMM."""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.inv.application.services import inventario_fisico_service
from app.modules.inv.presentation.schemas import (
    InventarioFisicoCreate,
    InventarioFisicoUpdate,
)

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
INVENTARIO_ID = uuid4()
ALMACEN_ID = uuid4()
USUARIO_ID = uuid4()


def _inv_create() -> InventarioFisicoCreate:
    return InventarioFisicoCreate(
        empresa_id=EMPRESA_ID,
        fecha_inventario=date(2026, 6, 12),
        almacen_id=ALMACEN_ID,
        tipo_inventario="total",
    )


def _inv_row(numero: str = "IF00001") -> dict:
    return {
        "inventario_fisico_id": INVENTARIO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_inventario": numero,
        "fecha_inventario": date(2026, 6, 12),
        "almacen_id": ALMACEN_ID,
        "tipo_inventario": "TOTAL",
        "estado": "en_proceso",
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
async def test_create_inventario_fisico_servicio_allocates_inv_inventario_fisico():
    session = AsyncMock()
    uow = _fake_uow(session)
    data = _inv_create()

    with patch(
        "app.modules.inv.application.services.inventario_fisico_service.enforce_body_empresa_matches_session",
        return_value=EMPRESA_ID,
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service.ensure_empresa_in_tenant",
        new_callable=AsyncMock,
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service._validate_cabecera_refs",
        new_callable=AsyncMock,
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service.unit_of_work",
        return_value=uow,
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service.InvCodigoGenerationService.resolve_codigo_for_create",
        new_callable=AsyncMock,
        return_value="IF00001",
    ) as mock_resolve, patch(
        "app.modules.inv.application.services.inventario_fisico_service.create_inventario_fisico",
        new_callable=AsyncMock,
        return_value=_inv_row(),
    ) as mock_create:
        result = await inventario_fisico_service.create_inventario_fisico_servicio(
            client_id=CLIENT_ID,
            data=data,
            usuario_id=USUARIO_ID,
        )

    mock_resolve.assert_awaited_once_with(
        "inv_inventario_fisico",
        session=session,
        client_id=CLIENT_ID,
        empresa_id=EMPRESA_ID,
        manual_code=None,
    )
    assert mock_create.await_args.kwargs["session"] is session
    assert mock_create.await_args.kwargs["data"]["numero_inventario"] == "IF00001"
    assert result.numero_inventario == "IF00001"


@pytest.mark.unit
def test_inventario_fisico_create_schema_excludes_numero_inventario():
    assert "numero_inventario" not in InventarioFisicoCreate.model_fields


@pytest.mark.unit
def test_inventario_fisico_update_schema_excludes_numero_inventario():
    assert "numero_inventario" not in InventarioFisicoUpdate.model_fields
    upd = InventarioFisicoUpdate.model_validate(
        {"descripcion": "x", "numero_inventario": "IF999"}
    )
    assert "numero_inventario" not in upd.model_dump(exclude_unset=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_inventario_fisico_servicio_does_not_call_motor():
    row = _inv_row()
    updated = {**row, "descripcion": "editado"}
    data = InventarioFisicoUpdate(descripcion="editado")

    with patch(
        "app.modules.inv.application.services.inventario_fisico_service.require_session_empresa_id",
        return_value=EMPRESA_ID,
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
        new_callable=AsyncMock,
        return_value=row,
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service.update_inventario_fisico",
        new_callable=AsyncMock,
        return_value=updated,
    ) as mock_upd, patch(
        "app.modules.inv.application.services.inventario_fisico_service.InvCodigoGenerationService.resolve_codigo_for_create",
        new_callable=AsyncMock,
    ) as mock_motor:
        result = await inventario_fisico_service.update_inventario_fisico_servicio(
            client_id=CLIENT_ID,
            inventario_fisico_id=INVENTARIO_ID,
            data=data,
        )

    payload = mock_upd.await_args.kwargs["data"]
    assert "numero_inventario" not in payload
    mock_motor.assert_not_awaited()
    assert result.numero_inventario == "IF00001"
