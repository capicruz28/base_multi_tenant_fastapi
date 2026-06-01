"""Tests Modelo Owner menú M2 — rol_menu_permiso sin bypass tenant_admin."""
from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.modules.modulos.application.services.modulo_menu_service import ModuloMenuService
from app.modules.modulos.presentation.schemas import MenuUsuarioResponse, ModuloMenuResponse


CLIENT_ID = uuid4()
USER_ID = uuid4()
ADMIN_ROL_ID = uuid4()
INV_MODULO_ID = UUID("E1000002-0000-4000-8000-000000000002")
INV_MENU_ID = uuid4()


def _inv_menu_row() -> Dict[str, Any]:
    return {
        "modulo_id": INV_MODULO_ID,
        "modulo_codigo": "INV",
        "modulo_nombre": "Inventarios",
        "modulo_descripcion": None,
        "modulo_icono": "inventory_2",
        "modulo_color": "#4CAF50",
        "modulo_categoria": "operaciones",
        "modulo_orden": 2,
        "seccion_id": uuid4(),
        "seccion_codigo": "PRINCIPAL",
        "seccion_nombre": "Principal",
        "seccion_descripcion": None,
        "seccion_icono": None,
        "seccion_orden": 1,
        "menu_id": INV_MENU_ID,
        "menu_codigo": "INV_PRODUCTOS",
        "menu_nombre": "Productos",
        "menu_descripcion": None,
        "menu_icono": None,
        "menu_ruta": "/inv/productos",
        "menu_padre_id": None,
        "menu_nivel": 1,
        "menu_tipo": "pantalla",
        "menu_orden": 1,
        "requiere_autenticacion": True,
        "menu_configuracion": None,
        "fecha_vencimiento": None,
        "modo_prueba": False,
        "limite_usuarios": None,
        "limite_registros": None,
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tenant_admin_uses_rol_menu_permiso_not_elevated():
    captured_queries: List[str] = []

    async def fake_execute_query(query, *args, **kwargs):
        q = query if isinstance(query, str) else str(query)
        captured_queries.append(q)
        conn = kwargs.get("connection_type")
        if conn is not None and "ADMIN" in str(conn):
            return [_inv_menu_row()]
        if "rol_menu_permiso" in q:
            return [
                {
                    "menu_id": INV_MENU_ID,
                    "puede_ver": 1,
                    "puede_crear": 1,
                    "puede_editar": 0,
                    "puede_eliminar": 0,
                    "puede_exportar": 0,
                    "puede_imprimir": 0,
                    "puede_aprobar": 0,
                }
            ]
        if "usuario_rol" in q:
            return [{"rol_id": ADMIN_ROL_ID, "es_activo": True}]
        return []

    fake_menu = MenuUsuarioResponse(
        modulos=[
            ModuloMenuResponse(
                modulo_id=INV_MODULO_ID,
                codigo="INV",
                nombre="Inventarios",
                color="#4CAF50",
                categoria="operaciones",
                orden=2,
            )
        ]
    )

    with patch(
        "app.modules.modulos.application.services.modulo_menu_service.execute_query",
        new=AsyncMock(side_effect=fake_execute_query),
    ), patch.object(
        ModuloMenuService,
        "_get_required_permissions_by_modulo",
        new=AsyncMock(return_value={}),
    ), patch(
        "app.modules.modulos.application.services.modulo_menu_service.transformar_sp_menu_usuario",
        return_value=fake_menu,
    ):
        await ModuloMenuService.obtener_menu_usuario(
            usuario_id=USER_ID,
            cliente_id=CLIENT_ID,
            as_tenant_admin=True,
            is_super_admin=False,
        )

    assert any("rol_menu_permiso" in q for q in captured_queries)
    assert not any("_menu_row_in_tenant_admin_scope" in q for q in captured_queries)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_super_admin_skips_rol_menu_permiso():
    captured_queries: List[str] = []

    async def fake_execute_query(query, *args, **kwargs):
        q = query if isinstance(query, str) else str(query)
        captured_queries.append(q)
        if kwargs.get("connection_type") and "ADMIN" in str(kwargs["connection_type"]):
            return [_inv_menu_row()]
        return []

    with patch(
        "app.modules.modulos.application.services.modulo_menu_service.execute_query",
        new=AsyncMock(side_effect=fake_execute_query),
    ), patch.object(
        ModuloMenuService,
        "_get_required_permissions_by_modulo",
        new=AsyncMock(return_value={}),
    ), patch(
        "app.modules.modulos.application.services.modulo_menu_service.transformar_sp_menu_usuario",
        return_value=MenuUsuarioResponse(modulos=[]),
    ):
        await ModuloMenuService.obtener_menu_usuario(
            usuario_id=USER_ID,
            cliente_id=CLIENT_ID,
            is_super_admin=True,
        )

    assert not any("rol_menu_permiso" in q for q in captured_queries)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_impersonation_uses_admin_tenant_rol_directly():
    captured_params: List[tuple] = []

    async def fake_execute_query(query, *args, **kwargs):
        q = query if isinstance(query, str) else str(query)
        if "SELECT rol_id" in q:
            return [{"rol_id": ADMIN_ROL_ID}]
        if kwargs.get("connection_type") and "ADMIN" in str(kwargs["connection_type"]):
            return [_inv_menu_row()]
        if "rol_menu_permiso" in q and kwargs.get("params"):
            captured_params.append(kwargs["params"])
            return [
                {
                    "menu_id": INV_MENU_ID,
                    "puede_ver": 1,
                    "puede_crear": 1,
                    "puede_editar": 0,
                    "puede_eliminar": 0,
                    "puede_exportar": 0,
                    "puede_imprimir": 0,
                    "puede_aprobar": 0,
                }
            ]
        return []

    with patch(
        "app.modules.modulos.application.services.modulo_menu_service.execute_query",
        new=AsyncMock(side_effect=fake_execute_query),
    ), patch.object(
        ModuloMenuService,
        "_get_required_permissions_by_modulo",
        new=AsyncMock(return_value={}),
    ), patch(
        "app.modules.modulos.application.services.modulo_menu_service.transformar_sp_menu_usuario",
        return_value=MenuUsuarioResponse(modulos=[]),
    ):
        await ModuloMenuService.obtener_menu_impersonacion_tenant(
            usuario_id=USER_ID,
            cliente_id=CLIENT_ID,
        )

    assert captured_params
    assert str(ADMIN_ROL_ID) in captured_params[0]
