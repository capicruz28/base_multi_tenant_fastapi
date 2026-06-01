from app.modules.tenant.application.services.user_standard_constants import (
    USER_STANDARD_MENU_GRANTS,
    USER_STANDARD_PERMISSION_CODIGOS,
)


def test_user_standard_permiso_count_is_16():
    assert len(USER_STANDARD_PERMISSION_CODIGOS) == 16


def test_user_standard_permissions_are_read_only():
    assert all(
        (c.endswith(".leer") or c in ("core.app.acceder", "tenant.branding.leer"))
        for c in USER_STANDARD_PERMISSION_CODIGOS
    )
    assert all((".crear" not in c) for c in USER_STANDARD_PERMISSION_CODIGOS)
    assert all((".actualizar" not in c) for c in USER_STANDARD_PERMISSION_CODIGOS)
    assert all((".eliminar" not in c) for c in USER_STANDARD_PERMISSION_CODIGOS)


def test_user_standard_menu_grants_count_is_14():
    assert len(USER_STANDARD_MENU_GRANTS) == 14


def test_user_standard_menu_grants_no_create_edit_delete():
    for _menu_id, flags in USER_STANDARD_MENU_GRANTS:
        assert int(flags.get("crear", 0)) == 0
        assert int(flags.get("editar", 0)) == 0
        assert int(flags.get("eliminar", 0)) == 0

