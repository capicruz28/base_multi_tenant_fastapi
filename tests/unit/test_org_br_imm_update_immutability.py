"""BR-IMM Fase 2 — inmutabilidad del código en UPDATE ORG (schemas + services)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.org.application.services import (
    cargo_service,
    centro_costo_service,
    departamento_service,
    empresa_service,
    sucursal_service,
)
from app.modules.org.presentation.schemas import (
    CargoUpdate,
    CentroCostoUpdate,
    DepartamentoUpdate,
    EmpresaUpdate,
    SucursalUpdate,
)

CLIENT_ID = uuid4()
EMPRESA_ID = uuid4()
ENTITY_ID = uuid4()
MONEDA_ID = uuid4()


# ----- SCH: schemas Update sin campo código (BR-IMM-01) -----


@pytest.mark.unit
@pytest.mark.parametrize(
    "schema_cls,forbidden",
    [
        (EmpresaUpdate, "codigo_empresa"),
        (SucursalUpdate, "codigo"),
        (DepartamentoUpdate, "codigo"),
        (CentroCostoUpdate, "codigo"),
        (CargoUpdate, "codigo"),
    ],
)
def test_org_update_schema_excludes_codigo_field(schema_cls, forbidden):
    assert forbidden not in schema_cls.model_fields


@pytest.mark.unit
def test_org_update_schema_ignores_extra_codigo_in_constructor():
    """Pydantic default: extras ignored — código en body no entra al modelo."""
    upd = CargoUpdate.model_validate({"nombre": "Nuevo", "codigo": "CAR999"})
    assert upd.nombre == "Nuevo"
    assert "codigo" not in upd.model_dump(exclude_unset=True)

    emp = EmpresaUpdate.model_validate(
        {"razon_social": "ACME", "codigo_empresa": "EMP999"}
    )
    assert emp.razon_social == "ACME"
    assert "codigo_empresa" not in emp.model_dump(exclude_unset=True)


# ----- IMM: update services nunca mutan código ni llaman motor -----


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_cargo_servicio_does_not_pass_codigo_or_call_motor():
    row = {
        "cargo_id": ENTITY_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CAR001",
        "nombre": "Analista",
        "moneda_salarial": MONEDA_ID,
        "es_activo": True,
    }
    updated = {**row, "nombre": "Analista Senior"}
    data = CargoUpdate(nombre="Analista Senior")

    with patch(
        "app.modules.org.application.services.cargo_service.require_session_empresa_id",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.cargo_service.get_cargo_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.org.application.services.cargo_service.update_cargo",
                new_callable=AsyncMock,
                return_value=updated,
            ) as mock_upd:
                with patch(
                    "app.modules.org.application.services.cargo_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                    new_callable=AsyncMock,
                ) as mock_motor:
                    with patch(
                        "app.modules.org.application.services.cargo_service.get_cargo_by_codigo",
                        new_callable=AsyncMock,
                    ) as mock_by_codigo:
                        result = await cargo_service.update_cargo_servicio(
                            client_id=CLIENT_ID, cargo_id=ENTITY_ID, data=data
                        )

    payload = mock_upd.await_args.kwargs["data"]
    assert "codigo" not in payload
    assert payload["nombre"] == "Analista Senior"
    mock_motor.assert_not_awaited()
    mock_by_codigo.assert_not_awaited()
    assert result.codigo == "CAR001"
    assert result.nombre == "Analista Senior"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_empresa_servicio_does_not_pass_codigo_empresa():
    row = {
        "empresa_id": EMPRESA_ID,
        "cliente_id": CLIENT_ID,
        "codigo_empresa": "EMP002",
        "razon_social": "ACME SA",
        "ruc": "20123456789",
        "es_activo": True,
    }
    updated = {**row, "razon_social": "ACME CORP"}
    data = EmpresaUpdate(razon_social="ACME CORP")

    with patch(
        "app.modules.org.application.services.empresa_service.get_empresa_by_id",
        new_callable=AsyncMock,
        return_value=row,
    ):
        with patch(
            "app.modules.org.application.services.empresa_service.update_empresa",
            new_callable=AsyncMock,
            return_value=updated,
        ) as mock_upd:
            with patch(
                "app.modules.org.application.services.empresa_service.OrgCodigoGenerationService.resolve_codigo_for_create",
                new_callable=AsyncMock,
            ) as mock_motor:
                with patch(
                    "app.modules.org.application.services.empresa_service.get_empresa_by_codigo",
                    new_callable=AsyncMock,
                ) as mock_by_codigo:
                    result = await empresa_service.update_empresa_servicio(
                        client_id=CLIENT_ID, empresa_id=EMPRESA_ID, data=data
                    )

    payload = mock_upd.await_args.kwargs["data"]
    assert "codigo_empresa" not in payload
    assert payload["razon_social"] == "ACME CORP"
    mock_motor.assert_not_awaited()
    mock_by_codigo.assert_not_awaited()
    assert result.codigo_empresa == "EMP002"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_sucursal_servicio_does_not_pass_codigo():
    row = {
        "sucursal_id": ENTITY_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "SUC001",
        "nombre": "Lima",
        "es_activo": True,
    }
    updated = {**row, "nombre": "Lima Centro"}
    data = SucursalUpdate(nombre="Lima Centro")

    with patch(
        "app.modules.org.application.services.sucursal_service.require_session_empresa_id",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.sucursal_service.get_sucursal_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.org.application.services.sucursal_service.update_sucursal",
                new_callable=AsyncMock,
                return_value=updated,
            ) as mock_upd:
                with patch(
                    "app.modules.org.application.services.sucursal_service.get_sucursal_by_codigo",
                    new_callable=AsyncMock,
                ) as mock_by_codigo:
                    result = await sucursal_service.update_sucursal_servicio(
                        client_id=CLIENT_ID, sucursal_id=ENTITY_ID, data=data
                    )

    assert "codigo" not in mock_upd.await_args.kwargs["data"]
    mock_by_codigo.assert_not_awaited()
    assert result.codigo == "SUC001"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_departamento_servicio_does_not_pass_codigo():
    row = {
        "departamento_id": ENTITY_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "DEP001",
        "nombre": "Ops",
        "es_activo": True,
    }
    updated = {**row, "nombre": "Operaciones"}
    data = DepartamentoUpdate(nombre="Operaciones")

    with patch(
        "app.modules.org.application.services.departamento_service.require_session_empresa_id",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.departamento_service.get_departamento_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.org.application.services.departamento_service.update_departamento",
                new_callable=AsyncMock,
                return_value=updated,
            ) as mock_upd:
                with patch(
                    "app.modules.org.application.services.departamento_service.get_departamento_by_codigo",
                    new_callable=AsyncMock,
                ) as mock_by_codigo:
                    result = await departamento_service.update_departamento_servicio(
                        client_id=CLIENT_ID, departamento_id=ENTITY_ID, data=data
                    )

    assert "codigo" not in mock_upd.await_args.kwargs["data"]
    mock_by_codigo.assert_not_awaited()
    assert result.codigo == "DEP001"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_centro_costo_servicio_does_not_pass_codigo():
    row = {
        "centro_costo_id": ENTITY_ID,
        "cliente_id": CLIENT_ID,
        "empresa_id": EMPRESA_ID,
        "codigo": "CC001",
        "nombre": "Admin",
        "tipo_centro_costo": "administrativo",
        "es_activo": True,
    }
    updated = {**row, "nombre": "Administración"}
    data = CentroCostoUpdate(nombre="Administración")

    with patch(
        "app.modules.org.application.services.centro_costo_service.require_session_empresa_id",
        return_value=EMPRESA_ID,
    ):
        with patch(
            "app.modules.org.application.services.centro_costo_service.get_centro_costo_by_id",
            new_callable=AsyncMock,
            return_value=row,
        ):
            with patch(
                "app.modules.org.application.services.centro_costo_service.update_centro_costo",
                new_callable=AsyncMock,
                return_value=updated,
            ) as mock_upd:
                with patch(
                    "app.modules.org.application.services.centro_costo_service.get_centro_costo_by_codigo",
                    new_callable=AsyncMock,
                ) as mock_by_codigo:
                    result = await centro_costo_service.update_centro_costo_servicio(
                        client_id=CLIENT_ID, centro_costo_id=ENTITY_ID, data=data
                    )

    assert "codigo" not in mock_upd.await_args.kwargs["data"]
    mock_by_codigo.assert_not_awaited()
    assert result.codigo == "CC001"
