"""Normalización rutas menú SaaS (/app/*)."""
from app.core.menu.menu_route_normalizer import normalize_menu_ruta_for_fe


def test_legacy_org_to_app():
    assert normalize_menu_ruta_for_fe("/org/empresa") == "/app/org/empresa"


def test_already_app_unchanged():
    assert normalize_menu_ruta_for_fe("/app/inv/productos") == "/app/inv/productos"


def test_admin_and_super_admin_unchanged():
    assert normalize_menu_ruta_for_fe("/admin/usuarios") == "/admin/usuarios"
    assert normalize_menu_ruta_for_fe("/super-admin/clientes") == "/super-admin/clientes"


def test_none_passthrough():
    assert normalize_menu_ruta_for_fe(None) is None
