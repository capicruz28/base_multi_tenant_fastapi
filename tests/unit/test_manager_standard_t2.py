from app.modules.tenant.application.services.manager_standard_constants import (
    MANAGER_STANDARD_MENU_GRANTS,
    MANAGER_STANDARD_PERMISSION_CODIGOS,
)


def test_manager_standard_permiso_count_is_47():
    assert len(MANAGER_STANDARD_PERMISSION_CODIGOS) == 47


def test_manager_standard_no_eliminar_permissions():
    assert all(
        (".eliminar" not in c) for c in MANAGER_STANDARD_PERMISSION_CODIGOS
    )


def test_manager_standard_empresa_is_read_only():
    assert "org.empresa.leer" in MANAGER_STANDARD_PERMISSION_CODIGOS
    assert "org.empresa.crear" not in MANAGER_STANDARD_PERMISSION_CODIGOS
    assert "org.empresa.actualizar" not in MANAGER_STANDARD_PERMISSION_CODIGOS
    assert "org.empresa.eliminar" not in MANAGER_STANDARD_PERMISSION_CODIGOS


def test_manager_standard_menu_grants_count_is_14():
    assert len(MANAGER_STANDARD_MENU_GRANTS) == 14


def test_manager_standard_menu_grants_no_delete():
    for _menu_id, flags in MANAGER_STANDARD_MENU_GRANTS:
        assert int(flags.get("eliminar", 0)) == 0

