"""Tests unitarios — PUT con-detalle inventario físico."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.modules.inv.application.services import inventario_fisico_service
from app.modules.inv.presentation.schemas import (
    InventarioFisicoConDetalleUpdate,
    InventarioFisicoDetalleCreateEmbebido,
)


CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
INVENTARIO_ID = uuid4()
PRODUCTO_ID = uuid4()


def _cabecera_row():
    return {
        "inventario_fisico_id": INVENTARIO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_inventario": "INV-FIS-001",
        "fecha_inventario": date(2026, 3, 1),
        "almacen_id": uuid4(),
        "tipo_inventario": "total",
        "estado": "en_proceso",
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_con_detalle_sin_empresa_id_en_schema_no_500():
    """Regresión: Update no expone empresa_id; empresa viene de sesión."""
    token = set_current_empresa_id(EMPRESA_ID)
    inv = _cabecera_row()
    det = InventarioFisicoDetalleCreateEmbebido(
        producto_id=PRODUCTO_ID,
        cantidad_sistema=Decimal("10"),
        cantidad_contada=Decimal("10"),
    )
    data = InventarioFisicoConDetalleUpdate(detalles=[det])
    assert not hasattr(data, "empresa_id")

    det_row = {
        "inventario_fisico_detalle_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "inventario_fisico_id": INVENTARIO_ID,
        "producto_id": PRODUCTO_ID,
        "cantidad_sistema": Decimal("10"),
        "cantidad_contada": Decimal("10"),
    }

    mock_uow = AsyncMock()
    mock_uow.execute = AsyncMock(
        side_effect=[
            {"rows_affected": 1},
            {"rows_affected": 1},
            [inv],
            [det_row],
        ]
    )

    class _FakeUowContext:
        async def __aenter__(self):
            return mock_uow

        async def __aexit__(self, *args):
            return False

    with patch(
        "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
        new=AsyncMock(return_value=inv),
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service._validate_detalle_productos",
        new=AsyncMock(),
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service.unit_of_work",
        return_value=_FakeUowContext(),
    ):
        result = await inventario_fisico_service.update_inventario_fisico_con_detalles_servicio(
            client_id=CLIENT_ID,
            inventario_fisico_id=INVENTARIO_ID,
            data=data,
        )

    assert result.inventario_fisico_id == INVENTARIO_ID
    assert len(result.detalles) == 1
    reset_current_empresa_id(token)
