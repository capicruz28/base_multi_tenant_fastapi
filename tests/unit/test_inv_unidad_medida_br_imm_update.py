"""BR-IMM — inmutabilidad del código en UPDATE inv_unidad_medida."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.inv.application.services import unidad_medida_service
from app.modules.inv.presentation.schemas import UnidadMedidaUpdate

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
UNIDAD_MEDIDA_ID = uuid4()


@pytest.mark.unit
def test_unidad_medida_update_schema_excludes_codigo_field():
    assert "codigo" not in UnidadMedidaUpdate.model_fields


@pytest.mark.unit
def test_unidad_medida_update_schema_ignores_extra_codigo_in_constructor():
    """Pydantic default: extras ignored — código en body no entra al modelo."""
    upd = UnidadMedidaUpdate.model_validate({"nombre": "Nuevo", "codigo": "UM999"})
    assert upd.nombre == "Nuevo"
    assert "codigo" not in upd.model_dump(exclude_unset=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_unidad_medida_servicio_does_not_pass_codigo_or_call_motor():
    row = {
        "unidad_medida_id": UNIDAD_MEDIDA_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "UM001",
        "nombre": "Kilogramo",
        "tipo_unidad": "PESO",
        "es_activo": True,
    }
    updated = {**row, "nombre": "Kilogramo Premium"}
    data = UnidadMedidaUpdate(nombre="Kilogramo Premium")

    with patch(
        "app.modules.inv.application.services.unidad_medida_service.require_session_empresa_id",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.unidad_medida_service.get_unidad_medida_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.inv.application.services.unidad_medida_service.update_unidad_medida",
                new_callable=AsyncMock,
                return_value=updated,
            ) as mock_upd:
                with patch(
                    "app.modules.inv.application.services.unidad_medida_service.InvCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                ) as mock_motor:
                    with patch(
                        "app.modules.inv.application.services.unidad_medida_service.get_unidad_medida_by_codigo",
                        new_callable=AsyncMock,
                    ) as mock_by_codigo:
                        result = await unidad_medida_service.update_unidad_medida_servicio(
                            client_id=CLIENT_ID,
                            unidad_medida_id=UNIDAD_MEDIDA_ID,
                            data=data,
                        )

    payload = mock_upd.await_args.kwargs["data"]
    assert "codigo" not in payload
    assert payload["nombre"] == "Kilogramo Premium"
    mock_motor.assert_not_awaited()
    mock_by_codigo.assert_not_awaited()
    assert result.codigo == "UM001"
    assert result.nombre == "Kilogramo Premium"
