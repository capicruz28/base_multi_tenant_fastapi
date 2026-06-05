"""Regression: desactivar_rol must return full RolRead fields, not rows_affected only."""
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.modules.rbac.application.services.rol_service import RolService


@pytest.mark.asyncio
async def test_desactivar_rol_returns_obtener_rol_por_id_after_update():
    rol_id = UUID("e933ad89-517c-4a3b-8519-c0920b13bbce")
    cliente_id = UUID("e4c8e906-0e64-4f4e-a04d-8daee57dc7f8")
    rol_activo = {
        "rol_id": rol_id,
        "cliente_id": cliente_id,
        "nombre": "QA_Rol",
        "descripcion": "test",
        "codigo_rol": None,
        "es_activo": True,
        "fecha_creacion": "2026-06-01T00:00:00",
    }
    rol_inactivo = {**rol_activo, "es_activo": False}

    with (
        patch(
            "app.core.tenant.context.get_current_client_id",
            return_value=cliente_id,
        ),
        patch(
            "app.modules.rbac.application.services.rol_service.execute_update",
            new_callable=AsyncMock,
            return_value={"rows_affected": 1},
        ),
        patch(
            "app.modules.rbac.application.services.rol_service.RolService.obtener_rol_por_id",
            new_callable=AsyncMock,
            side_effect=[rol_activo, rol_inactivo],
        ) as mock_get,
    ):
        result = await RolService.desactivar_rol(rol_id)

    assert mock_get.await_count == 2
    assert mock_get.await_args_list[1].kwargs.get("incluir_inactivos") is True
    assert result["rol_id"] == rol_id
    assert result["nombre"] == "QA_Rol"
    assert result["es_activo"] is False
    assert "rows_affected" not in result
