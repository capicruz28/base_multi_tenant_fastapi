"""F-002: Superadmin global users list accepts UUID cliente_id query param."""
import inspect
from typing import Optional, get_args, get_origin
from uuid import UUID

import pytest


def _annotation_includes_uuid(annotation) -> bool:
    if annotation is UUID:
        return True
    if get_origin(annotation) is not None:
        return UUID in get_args(annotation)
    return "UUID" in str(annotation)


def test_list_usuarios_global_cliente_id_annotation_is_uuid():
    from app.modules.superadmin.presentation.endpoints_usuarios import list_usuarios_global

    param = inspect.signature(list_usuarios_global).parameters["cliente_id"]
    assert _annotation_includes_uuid(param.annotation)


def test_superadmin_usuario_service_list_global_accepts_uuid():
    from app.modules.superadmin.application.services.superadmin_usuario_service import (
        SuperadminUsuarioService,
    )

    param = inspect.signature(SuperadminUsuarioService.get_usuarios_globales).parameters[
        "cliente_id"
    ]
    assert _annotation_includes_uuid(param.annotation)


@pytest.mark.unit
def test_auth_config_uses_lbac_not_role_checker():
    import app.modules.auth.presentation.endpoints_auth_config as mod

    source = inspect.getsource(mod)
    assert "lbac" in source or "require_super_admin" in source
    assert "RoleChecker" not in source
    assert "SUPER_ADMIN" not in source or "Super Administrador" in source
