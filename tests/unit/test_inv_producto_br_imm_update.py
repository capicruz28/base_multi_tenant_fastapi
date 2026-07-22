"""BR-IMM — inmutabilidad de codigo_sku en UPDATE inv_producto."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.inv.application.services import producto_service
from app.modules.inv.presentation.schemas import ProductoUpdate

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
PRODUCTO_ID = uuid4()
UNIDAD_MEDIDA_ID = uuid4()
MONEDA_ID = uuid4()


@pytest.mark.unit
def test_producto_update_schema_excludes_codigo_sku_field():
    assert "codigo_sku" not in ProductoUpdate.model_fields


@pytest.mark.unit
def test_producto_update_schema_ignores_extra_codigo_sku_in_constructor():
    """Pydantic default: extras ignored — codigo_sku en body no entra al modelo."""
    upd = ProductoUpdate.model_validate({"nombre": "Nuevo", "codigo_sku": "SKU999"})
    assert upd.nombre == "Nuevo"
    assert "codigo_sku" not in upd.model_dump(exclude_unset=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_producto_servicio_does_not_pass_codigo_sku_or_call_motor():
    row = {
        "producto_id": PRODUCTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo_sku": "P00001",
        "nombre": "Producto test",
        "tipo_producto": "BIEN",
        "unidad_medida_base_id": UNIDAD_MEDIDA_ID,
        "moneda_costo": MONEDA_ID,
        "moneda_venta": MONEDA_ID,
        "es_activo": True,
    }
    updated = {**row, "nombre": "Producto Premium"}
    data = ProductoUpdate(nombre="Producto Premium")

    with patch(
        "app.modules.inv.application.services.producto_service.require_session_empresa_id",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.producto_service.get_producto_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.inv.application.services.producto_service._validate_producto_referencias_empresa",
                new_callable=AsyncMock,
            ):
                with patch(
                    "app.modules.inv.application.services.producto_service.update_producto",
                    new_callable=AsyncMock,
                    return_value=updated,
                ) as mock_upd:
                    with patch(
                        "app.modules.inv.application.services.producto_service.InvCodigoGenerationService.resolve_codigo_for_create",
                        new_callable=AsyncMock,
                    ) as mock_motor:
                        with patch(
                            "app.modules.inv.application.services.producto_service.get_producto_by_sku",
                            new_callable=AsyncMock,
                        ) as mock_by_sku:
                            result = await producto_service.update_producto_servicio(
                                client_id=CLIENT_ID,
                                producto_id=PRODUCTO_ID,
                                data=data,
                            )

    payload = mock_upd.await_args.kwargs["data"]
    assert "codigo_sku" not in payload
    assert payload["nombre"] == "Producto Premium"
    mock_motor.assert_not_awaited()
    mock_by_sku.assert_not_awaited()
    assert result.codigo_sku == "P00001"
    assert result.nombre == "Producto Premium"
