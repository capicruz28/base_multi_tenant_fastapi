"""Tests P1 — buscar SQL en maestros INV."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import pytest

from app.core.tenant.empresa_context import reset_current_empresa_id, set_current_empresa_id
from app.modules.inv.application.services import (
    categoria_service,
    almacen_service,
    unidad_medida_service,
    tipo_movimiento_service,
)

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()


def _categoria_row():
    return {
        "categoria_id": uuid4(),
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CAT01",
        "nombre": "Categoria test",
        "es_activo": True,
        "fecha_creacion": datetime.utcnow(),
    }


@pytest.mark.asyncio
async def test_categorias_buscar_passed_to_query():
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        with patch(
            "app.modules.inv.application.services.categoria_service.list_categorias",
            new_callable=AsyncMock,
            return_value=[_categoria_row()],
        ) as mock_list:
            result = await categoria_service.list_categorias_servicio(
                client_id=CLIENT_ID,
                buscar="cat",
            )
        assert isinstance(result, list)
        mock_list.assert_awaited_once_with(
            client_id=CLIENT_ID,
            empresa_id=EMPRESA_ID,
            solo_activos=True,
            buscar="cat",
        )
    finally:
        reset_current_empresa_id(token)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "service_module,list_fn",
    [
        ("almacen_service", "list_almacenes"),
        ("unidad_medida_service", "list_unidades_medida"),
        ("tipo_movimiento_service", "list_tipos_movimiento"),
    ],
)
async def test_inv_maestros_buscar_forwarded(service_module, list_fn):
    token = set_current_empresa_id(EMPRESA_ID)
    try:
        patch_target = f"app.modules.inv.application.services.{service_module}.{list_fn}"
        service = {
            "almacen_service": almacen_service,
            "unidad_medida_service": unidad_medida_service,
            "tipo_movimiento_service": tipo_movimiento_service,
        }[service_module]
        list_servicio = getattr(service, f"list_{list_fn.split('_', 1)[1]}_servicio")
        with patch(patch_target, new_callable=AsyncMock, return_value=[]) as mock_list:
            await list_servicio(client_id=CLIENT_ID, buscar="xyz")
        assert mock_list.await_args.kwargs.get("buscar") == "xyz"
    finally:
        reset_current_empresa_id(token)
