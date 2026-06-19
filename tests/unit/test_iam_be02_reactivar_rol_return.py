"""IAM-BE-02: reactivar_rol debe retornar RolRead, no rows_affected del UPDATE."""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.rbac.application.services.rol_service import RolService

ROL_ID = uuid4()
ROL_INACTIVO = {
    "rol_id": ROL_ID,
    "nombre": "Operador",
    "descripcion": "Rol operativo",
    "es_activo": False,
    "fecha_creacion": "2026-01-01T00:00:00",
    "cliente_id": uuid4(),
    "codigo_rol": "OPERADOR",
    "nivel_acceso": 2,
}
ROL_REACTIVADO = {**ROL_INACTIVO, "es_activo": True}


@pytest.mark.asyncio
async def test_reactivar_rol_returns_rol_read_after_update():
    with (
        patch.object(
            RolService,
            "obtener_rol_por_id",
            new_callable=AsyncMock,
            side_effect=[ROL_INACTIVO, ROL_REACTIVADO],
        ),
        patch(
            "app.core.tenant.context.get_current_client_id",
            return_value=ROL_INACTIVO["cliente_id"],
        ),
        patch(
            "app.modules.rbac.application.services.rol_service.execute_update",
            new_callable=AsyncMock,
            return_value={"rows_affected": 1},
        ),
    ):
        result = await RolService.reactivar_rol(rol_id=ROL_ID)

    assert result["rol_id"] == ROL_ID
    assert result["es_activo"] is True
    assert "rows_affected" not in result


@pytest.mark.asyncio
async def test_reactivar_rol_idempotent_when_already_active():
    with (
        patch.object(
            RolService,
            "obtener_rol_por_id",
            new_callable=AsyncMock,
            return_value=ROL_REACTIVADO,
        ),
        patch(
            "app.modules.rbac.application.services.rol_service.execute_update",
            new_callable=AsyncMock,
        ) as mock_update,
    ):
        result = await RolService.reactivar_rol(rol_id=ROL_ID)

    mock_update.assert_not_called()
    assert result["es_activo"] is True
