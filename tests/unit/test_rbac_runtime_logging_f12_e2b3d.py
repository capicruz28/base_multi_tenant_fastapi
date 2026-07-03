"""F12-E2B3D — tests de política de logging RBAC runtime."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.core.authorization import rbac
from app.core.authorization.rbac import AuthorizationError, require_permission


def _mock_user(*, permisos=None, is_super_admin=False, nombre="admin"):
    roles = []
    if is_super_admin:
        roles = [SimpleNamespace(nombre="SuperAdministrador", es_activo=True, fecha_asignacion=True)]
    return SimpleNamespace(
        nombre_usuario=nombre,
        is_super_admin=is_super_admin,
        roles=roles,
        permisos=permisos or ["admin.usuario.leer"],
        user_type="tenant_admin" if not is_super_admin else "platform_admin",
        access_level=5 if is_super_admin else 1,
        cliente=None,
    )


@pytest.mark.unit
class TestRbacRuntimeLoggingPolicy:
    def test_require_permission_success_emits_no_info_when_not_verbose(self):
        user = _mock_user(permisos=["admin.usuario.leer"])
        dep = require_permission("admin.usuario.leer")

        with patch("app.core.authorization.rbac.settings") as mock_settings:
            mock_settings.ENABLE_AUTH_VERBOSE = False
            mock_settings.ENABLE_RBAC_TRACE = False
            with patch.object(rbac, "get_current_active_user", return_value=user):
                with patch.object(rbac.logger, "info") as mock_info:
                    with patch.object(rbac.logger, "warning") as mock_warn:
                        with patch.object(rbac.logger, "debug") as mock_debug:
                            result = dep(current_user=user)

        assert result is user
        mock_info.assert_not_called()
        mock_warn.assert_not_called()
        assert mock_debug.call_count >= 2

    def test_require_permission_denied_emits_warning_only(self):
        user = _mock_user(permisos=["admin.rol.leer"])
        dep = require_permission("admin.usuario.leer")

        with patch("app.core.authorization.rbac.settings") as mock_settings:
            mock_settings.ENABLE_AUTH_VERBOSE = False
            mock_settings.ENABLE_RBAC_TRACE = False
            with patch.object(rbac, "get_current_active_user", return_value=user):
                with patch.object(rbac.logger, "info") as mock_info:
                    with patch.object(rbac.logger, "warning") as mock_warn:
                        with pytest.raises(AuthorizationError):
                            dep(current_user=user)

        mock_info.assert_not_called()
        assert mock_warn.call_count == 1
        assert "Intento de acceso sin permiso" in str(mock_warn.call_args.args[0])

    def test_get_user_type_super_admin_diagnostic_when_auth_verbose(self):
        user = _mock_user(is_super_admin=True)

        with patch("app.core.authorization.rbac.settings") as mock_settings:
            mock_settings.ENABLE_AUTH_VERBOSE = True
            with patch.object(rbac.logger, "info") as mock_info:
                user_type = rbac.get_user_type(user)

        assert user_type == "super_admin"
        assert any("SUPER ADMIN" in str(c.args[0]) for c in mock_info.call_args_list)
