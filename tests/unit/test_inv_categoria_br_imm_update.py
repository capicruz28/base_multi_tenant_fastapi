"""BR-IMM — inmutabilidad del código en UPDATE inv_categoria_producto."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.inv.application.services import categoria_service
from app.modules.inv.presentation.schemas import CategoriaUpdate

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
CATEGORIA_ID = uuid4()


@pytest.mark.unit
def test_categoria_update_schema_excludes_codigo_field():
    assert "codigo" not in CategoriaUpdate.model_fields


@pytest.mark.unit
def test_categoria_update_schema_ignores_extra_codigo_in_constructor():
    """Pydantic default: extras ignored — código en body no entra al modelo."""
    upd = CategoriaUpdate.model_validate({"nombre": "Nuevo", "codigo": "CAT999"})
    assert upd.nombre == "Nuevo"
    assert "codigo" not in upd.model_dump(exclude_unset=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_categoria_servicio_does_not_pass_codigo_or_call_motor():
    row = {
        "categoria_id": CATEGORIA_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CAT001",
        "nombre": "Electrónica",
        "es_activo": True,
    }
    updated = {**row, "nombre": "Electrónica Premium"}
    data = CategoriaUpdate(nombre="Electrónica Premium")

    with patch(
        "app.modules.inv.application.services.categoria_service.require_session_empresa_id",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.inv.application.services.categoria_service.get_categoria_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.inv.application.services.categoria_service.update_categoria",
                new_callable=AsyncMock,
                return_value=updated,
            ) as mock_upd:
                with patch(
                    "app.modules.inv.application.services.categoria_service.InvCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                ) as mock_motor:
                    with patch(
                        "app.modules.inv.application.services.categoria_service.get_categoria_by_codigo",
                        new_callable=AsyncMock,
                    ) as mock_by_codigo:
                        result = await categoria_service.update_categoria_servicio(
                            client_id=CLIENT_ID,
                            categoria_id=CATEGORIA_ID,
                            data=data,
                        )

    payload = mock_upd.await_args.kwargs["data"]
    assert "codigo" not in payload
    assert payload["nombre"] == "Electrónica Premium"
    mock_motor.assert_not_awaited()
    mock_by_codigo.assert_not_awaited()
    assert result.codigo == "CAT001"
    assert result.nombre == "Electrónica Premium"
