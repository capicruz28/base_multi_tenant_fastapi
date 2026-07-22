"""BR-IMM — inmutabilidad del código en UPDATE inv_tipo_movimiento."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.inv.application.services import tipo_movimiento_service
from app.modules.inv.presentation.schemas import TipoMovimientoUpdate

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
TIPO_MOVIMIENTO_ID = uuid4()


@pytest.mark.unit
def test_tipo_movimiento_update_schema_excludes_codigo_field():
    assert "codigo" not in TipoMovimientoUpdate.model_fields


@pytest.mark.unit
def test_tipo_movimiento_update_schema_ignores_extra_codigo_in_constructor():
    """Pydantic default: extras ignored — código en body no entra al modelo."""
    upd = TipoMovimientoUpdate.model_validate({"nombre": "Nuevo", "codigo": "TM999"})
    assert upd.nombre == "Nuevo"
    assert "codigo" not in upd.model_dump(exclude_unset=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_tipo_movimiento_servicio_does_not_pass_codigo_or_call_motor():
    row = {
        "tipo_movimiento_id": TIPO_MOVIMIENTO_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "TM001",
        "nombre": "Entrada compra",
        "clase_movimiento": "ENTRADA",
        "es_activo": True,
    }
    updated = {**row, "nombre": "Entrada compra premium"}
    data = TipoMovimientoUpdate(nombre="Entrada compra premium")

    with patch(
        "app.modules.inv.application.services.tipo_movimiento_service.require_session_empresa_id",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.tipo_movimiento_service.get_tipo_movimiento_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.inv.application.services.tipo_movimiento_service.update_tipo_movimiento",
                new_callable=AsyncMock,
                return_value=updated,
            ) as mock_upd:
                with patch(
                    "app.modules.inv.application.services.tipo_movimiento_service.InvCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                ) as mock_motor:
                    with patch(
                        "app.modules.inv.application.services.tipo_movimiento_service.get_tipo_movimiento_by_codigo",
                        new_callable=AsyncMock,
                    ) as mock_by_codigo:
                        result = await tipo_movimiento_service.update_tipo_movimiento_servicio(
                            client_id=CLIENT_ID,
                            tipo_movimiento_id=TIPO_MOVIMIENTO_ID,
                            data=data,
                        )

    payload = mock_upd.await_args.kwargs["data"]
    assert "codigo" not in payload
    assert payload["nombre"] == "Entrada compra premium"
    mock_motor.assert_not_awaited()
    mock_by_codigo.assert_not_awaited()
    assert result.codigo == "TM001"
    assert result.nombre == "Entrada compra premium"
