"""
Tests unitarios — F4: conteo completo obligatorio antes de finalizar.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.modules.inv.application.services import inventario_fisico_service
from app.modules.inv.application.services.inventario_fisico_service import (
    _count_lineas_conteo_pendiente,
)


CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
INVENTARIO_ID = uuid4()


def _base_inv(*, estado: str = "en_proceso") -> dict:
    return {
        "inventario_fisico_id": INVENTARIO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "numero_inventario": "INV-FIS-001",
        "fecha_inventario": date(2026, 3, 1),
        "almacen_id": uuid4(),
        "tipo_inventario": "total",
        "estado": estado,
    }


def _detalle(contada) -> dict:
    return {
        "producto_id": uuid4(),
        "cantidad_sistema": Decimal("10"),
        "cantidad_contada": contada,
    }


@pytest.mark.unit
def test_count_lineas_conteo_pendiente_cero_es_valido():
    detalles = [_detalle(Decimal("0")), _detalle(Decimal("5"))]
    assert _count_lineas_conteo_pendiente(detalles) == 0


@pytest.mark.unit
def test_count_lineas_conteo_pendiente_null_es_pendiente():
    detalles = [_detalle(Decimal("0")), _detalle(None), _detalle(Decimal("3"))]
    assert _count_lineas_conteo_pendiente(detalles) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_finalizar_con_pendientes_422():
    token = set_current_empresa_id(EMPRESA_ID)
    inv = _base_inv()
    detalles = [_detalle(Decimal("1")), _detalle(None), _detalle(None)]

    with patch(
        "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
        new=AsyncMock(return_value=inv),
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_con_detalles",
        new=AsyncMock(return_value={**inv, "detalles": detalles}),
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service.update_inventario_fisico",
        new=AsyncMock(),
    ) as mock_update:
        with pytest.raises(HTTPException) as exc:
            await inventario_fisico_service.finalizar_inventario_fisico_servicio(
                client_id=CLIENT_ID,
                inventario_fisico_id=INVENTARIO_ID,
            )

    assert exc.value.status_code == 422
    assert "2 línea(s) pendiente(s)" in exc.value.detail
    mock_update.assert_not_called()
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_finalizar_todas_contadas_incluye_cero():
    token = set_current_empresa_id(EMPRESA_ID)
    inv = _base_inv()
    detalles = [_detalle(Decimal("0")), _detalle(Decimal("10"))]
    finalized = {**inv, "estado": "finalizado"}

    with patch(
        "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
        new=AsyncMock(return_value=inv),
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_con_detalles",
        new=AsyncMock(return_value={**inv, "detalles": detalles}),
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service.update_inventario_fisico",
        new=AsyncMock(return_value=finalized),
    ) as mock_update:
        result = await inventario_fisico_service.finalizar_inventario_fisico_servicio(
            client_id=CLIENT_ID,
            inventario_fisico_id=INVENTARIO_ID,
        )

    assert result.estado == "finalizado"
    mock_update.assert_called_once()
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_finalizar_sin_detalle_422():
    token = set_current_empresa_id(EMPRESA_ID)
    inv = _base_inv()

    with patch(
        "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
        new=AsyncMock(return_value=inv),
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_con_detalles",
        new=AsyncMock(return_value={**inv, "detalles": []}),
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service.update_inventario_fisico",
        new=AsyncMock(),
    ) as mock_update:
        with pytest.raises(HTTPException) as exc:
            await inventario_fisico_service.finalizar_inventario_fisico_servicio(
                client_id=CLIENT_ID,
                inventario_fisico_id=INVENTARIO_ID,
            )

    assert exc.value.status_code == 422
    assert "sin detalle" in exc.value.detail.lower()
    mock_update.assert_not_called()
    reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_finalizar_ya_finalizado_idempotente_sin_revalidar_f4():
    token = set_current_empresa_id(EMPRESA_ID)
    inv = _base_inv(estado="finalizado")

    with patch(
        "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_by_id",
        new=AsyncMock(return_value=inv),
    ), patch(
        "app.modules.inv.application.services.inventario_fisico_service.get_inventario_fisico_con_detalles",
        new=AsyncMock(),
    ) as mock_con_detalle, patch(
        "app.modules.inv.application.services.inventario_fisico_service.update_inventario_fisico",
        new=AsyncMock(),
    ) as mock_update:
        result = await inventario_fisico_service.finalizar_inventario_fisico_servicio(
            client_id=CLIENT_ID,
            inventario_fisico_id=INVENTARIO_ID,
        )

    assert result.estado == "finalizado"
    mock_con_detalle.assert_not_called()
    mock_update.assert_not_called()
    reset_current_empresa_id(token)
