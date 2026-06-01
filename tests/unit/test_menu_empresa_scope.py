"""
I2.1: menú filtrado por empresa_id de sesión (rol_menu_permiso ⋈ usuario_rol).
"""
from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.core.tenant.empresa_context import (
    resolve_empresa_id,
    sql_empresa_filter_usuario_rol,
    sql_empresa_filter_usuario_rol_qmark,
)
from app.modules.modulos.application.services.modulo_menu_service import ModuloMenuService
from app.modules.modulos.presentation.schemas import MenuUsuarioResponse

CLIENT_ID = uuid4()
USER_ID = uuid4()
EMPRESA_A = uuid4()
EMPRESA_B = uuid4()
MENU_ID = uuid4()
MODULO_ID = uuid4()


def _menu_central_row() -> Dict[str, Any]:
    return {
        "modulo_id": MODULO_ID,
        "modulo_codigo": "INV",
        "modulo_nombre": "Inventario",
        "modulo_descripcion": None,
        "modulo_icono": "box",
        "modulo_color": None,
        "modulo_categoria": None,
        "modulo_orden": 1,
        "seccion_id": None,
        "seccion_codigo": None,
        "seccion_nombre": None,
        "seccion_descripcion": None,
        "seccion_icono": None,
        "seccion_orden": None,
        "menu_id": MENU_ID,
        "menu_codigo": "inv_prod",
        "menu_nombre": "Productos",
        "menu_descripcion": None,
        "menu_icono": None,
        "menu_ruta": "/inv/productos",
        "menu_padre_id": None,
        "menu_nivel": 1,
        "menu_tipo": "item",
        "menu_orden": 1,
        "requiere_autenticacion": True,
        "menu_configuracion": None,
        "fecha_vencimiento": None,
        "modo_prueba": False,
        "limite_usuarios": None,
        "limite_registros": None,
    }


@pytest.mark.unit
def test_sql_empresa_filter_named_and_qmark_equivalent_semantics():
    named = sql_empresa_filter_usuario_rol("ur")
    qmark = sql_empresa_filter_usuario_rol_qmark("ur")
    assert "ur.empresa_id IS NULL" in named
    assert "ur.empresa_id = :empresa_id" in named
    assert "ur.empresa_id IS NULL" in qmark
    assert "ur.empresa_id = ?" in qmark


@pytest.mark.unit
def test_resolve_empresa_id_prefers_explicit_over_context():
    token = None
    try:
        from app.core.tenant import empresa_context

        token = empresa_context.set_current_empresa_id(EMPRESA_A)
        assert resolve_empresa_id(EMPRESA_B) == EMPRESA_B
        assert resolve_empresa_id(None) == EMPRESA_A
    finally:
        if token is not None:
            from app.core.tenant import empresa_context

            empresa_context.reset_current_empresa_id(token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_obtener_menu_usuario_sql_includes_empresa_filter_when_scoped():
    captured: Dict[str, Any] = {}

    async def fake_execute_query(query, *args, **kwargs):
        q = query if isinstance(query, str) else str(query)
        if "rol_menu_permiso" in q:
            captured["permiso_sql"] = q
            captured["permiso_params"] = kwargs.get("params")
            return [
                {
                    "menu_id": MENU_ID,
                    "puede_ver": 1,
                    "puede_crear": 0,
                    "puede_editar": 0,
                    "puede_eliminar": 0,
                    "puede_exportar": 0,
                    "puede_imprimir": 0,
                    "puede_aprobar": 0,
                }
            ]
        if kwargs.get("connection_type") and "ADMIN" in str(kwargs.get("connection_type")):
            return [_menu_central_row()]
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
            empresa_id=EMPRESA_A,
        )

    assert "ur.empresa_id IS NULL" in captured["permiso_sql"]
    assert "ur.empresa_id = ?" in captured["permiso_sql"]
    assert str(EMPRESA_A) in captured["permiso_params"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_obtener_menu_usuario_sql_omits_empresa_filter_without_session_empresa():
    captured: Dict[str, Any] = {}

    async def fake_execute_query(query, *args, **kwargs):
        q = query if isinstance(query, str) else str(query)
        if "rol_menu_permiso" in q:
            captured["permiso_sql"] = q
            return [{"menu_id": MENU_ID, "puede_ver": 1, "puede_crear": 0, "puede_editar": 0,
                     "puede_eliminar": 0, "puede_exportar": 0, "puede_imprimir": 0, "puede_aprobar": 0}]
        conn = kwargs.get("connection_type")
        if conn is not None and "ADMIN" in str(conn):
            return [_menu_central_row()]
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
            empresa_id=None,
        )

    assert "ur.empresa_id" not in captured.get("permiso_sql", "")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_obtener_menu_usuario_tenant_admin_uses_rmp_sql():
    """Modelo Owner: tenant_admin ya no omite rol_menu_permiso."""
    captured_queries: List[str] = []

    async def fake_execute_query(query, *args, **kwargs):
        q = query if isinstance(query, str) else str(query)
        captured_queries.append(q)
        conn = kwargs.get("connection_type")
        if conn is not None and "ADMIN" in str(conn):
            return [_menu_central_row()]
        if "rol_menu_permiso" in q:
            return [
                {
                    "menu_id": uuid4(),
                    "puede_ver": 1,
                    "puede_crear": 0,
                    "puede_editar": 0,
                    "puede_eliminar": 0,
                    "puede_exportar": 0,
                    "puede_imprimir": 0,
                    "puede_aprobar": 0,
                }
            ]
        return [{"rol_id": uuid4(), "es_activo": True}]

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
            as_tenant_admin=True,
            empresa_id=EMPRESA_A,
        )

    assert any("rol_menu_permiso" in q for q in captured_queries)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cross_company_simulation_different_menu_ids_per_empresa():
    """Simula: rol menú A solo visible con filtro EMPRESA_A, no con EMPRESA_B."""
    menu_a = uuid4()
    menu_b = uuid4()

    rol_diag = uuid4()

    async def fake_execute_query(query, *args, **kwargs):
        q = query if isinstance(query, str) else str(query)
        if "rol_menu_permiso" in q:
            params = kwargs.get("params") or ()
            empresa_in_params = str(EMPRESA_A) in params
            mid = menu_a if empresa_in_params else menu_b
            if str(EMPRESA_B) in params and str(EMPRESA_A) not in params:
                return []
            return [
                {
                    "menu_id": mid,
                    "puede_ver": 1,
                    "puede_crear": 0,
                    "puede_editar": 0,
                    "puede_eliminar": 0,
                    "puede_exportar": 0,
                    "puede_imprimir": 0,
                    "puede_aprobar": 0,
                }
            ]
        conn = kwargs.get("connection_type")
        if conn is not None and "ADMIN" in str(conn):
            row = _menu_central_row()
            return [{**row, "menu_id": menu_a}]
        return [{"rol_id": rol_diag, "es_activo": True}]

    transform_calls: List[Dict[str, Any]] = []

    def capture_transform(rows, **kwargs):
        transform_calls.append({"rows": rows})
        return MenuUsuarioResponse(modulos=[])

    with patch(
        "app.modules.modulos.application.services.modulo_menu_service.execute_query",
        new=AsyncMock(side_effect=fake_execute_query),
    ), patch.object(
        ModuloMenuService,
        "_get_required_permissions_by_modulo",
        new=AsyncMock(return_value={}),
    ), patch(
        "app.modules.modulos.application.services.modulo_menu_service.transformar_sp_menu_usuario",
        side_effect=capture_transform,
    ):
        await ModuloMenuService.obtener_menu_usuario(
            USER_ID, CLIENT_ID, empresa_id=EMPRESA_A
        )
        result_b = await ModuloMenuService.obtener_menu_usuario(
            USER_ID, CLIENT_ID, empresa_id=EMPRESA_B
        )

    assert len(transform_calls) == 1
    assert len(transform_calls[0]["rows"]) >= 1
    assert result_b.modulos == []
