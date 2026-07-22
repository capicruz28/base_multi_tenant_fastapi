"""BR-IMM — inmutabilidad del código en UPDATE inv_almacen."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.inv.application.services import almacen_service
from app.modules.inv.presentation.schemas import AlmacenUpdate

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
ALMACEN_ID = uuid4()


@pytest.mark.unit
def test_almacen_update_schema_excludes_codigo_field():
    assert "codigo" not in AlmacenUpdate.model_fields


@pytest.mark.unit
def test_almacen_update_schema_ignores_extra_codigo_in_constructor():
    """Pydantic default: extras ignored — código en body no entra al modelo."""
    upd = AlmacenUpdate.model_validate({"nombre": "Nuevo", "codigo": "ALM999"})
    assert upd.nombre == "Nuevo"
    assert "codigo" not in upd.model_dump(exclude_unset=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_almacen_servicio_does_not_pass_codigo_or_call_motor():
    row = {
        "almacen_id": ALMACEN_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "ALM001",
        "nombre": "Almacen central",
        "tipo_almacen": "GENERAL",
        "es_activo": True,
    }
    updated = {**row, "nombre": "Almacen principal"}
    data = AlmacenUpdate(nombre="Almacen principal")

    with patch(
        "app.modules.inv.application.services.almacen_service.require_session_empresa_id",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.almacen_service.get_almacen_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.inv.application.services.almacen_service.update_almacen",
                new_callable=AsyncMock,
                return_value=updated,
            ) as mock_upd:
                with patch(
                    "app.modules.inv.application.services.almacen_service.InvCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                ) as mock_motor:
                    with patch(
                        "app.modules.inv.application.services.almacen_service.get_almacen_by_codigo",
                        new_callable=AsyncMock,
                    ) as mock_by_codigo:
                        result = await almacen_service.update_almacen_servicio(
                            client_id=CLIENT_ID,
                            almacen_id=ALMACEN_ID,
                            data=data,
                        )

    payload = mock_upd.await_args.kwargs["data"]
    assert "codigo" not in payload
    assert payload["nombre"] == "Almacen principal"
    mock_motor.assert_not_awaited()
    mock_by_codigo.assert_not_awaited()
    assert result.codigo == "ALM001"
    assert result.nombre == "Almacen principal"
