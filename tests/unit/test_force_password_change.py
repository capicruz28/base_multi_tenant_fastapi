"""
Tests unitarios — FORCE PASSWORD CHANGE (estrategia O5).
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import Request

from app.core.auth.password_change_enforcement import (
    PASSWORD_CHANGE_REQUIRED_CODE,
    enforce_password_change_policy,
    is_auth_route_whitelisted,
    is_excluded_from_password_change_enforcement,
    resolve_requires_password_change_from_user,
)
from app.core.exceptions import AuthorizationError
from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.presentation.schemas import (
    PasswordChangeRequest,
    UserDataWithRoles,
    build_user_data_with_roles_dict,
)


def _request(method: str, path: str) -> Request:
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [],
    }
    return Request(scope)


def _usuario(
    *,
    requiere_cambio: bool = True,
    proveedor: str = "local",
    user_type: str = "tenant_admin",
    is_super_admin: bool = False,
    nombre_usuario: str = "admin",
):
    return SimpleNamespace(
        requiere_cambio_contrasena=requiere_cambio,
        proveedor_autenticacion=proveedor,
        user_type=user_type,
        is_super_admin=is_super_admin,
        nombre_usuario=nombre_usuario,
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "method,path,expected",
    [
        ("POST", "/api/v1/auth/password/change/", True),
        ("GET", "/api/v1/auth/me/", True),
        ("POST", "/api/v1/auth/logout/", True),
        ("POST", "/api/v1/auth/refresh/", True),
        ("POST", "/api/v1/auth/empresa/seleccionar/", True),
        ("POST", f"/api/v1/auth/impersonate/{uuid4()}/", True),
        ("POST", "/api/v1/auth/impersonate/end/", True),
        ("GET", "/api/v1/fin/asientos/", False),
        ("POST", "/api/v1/auth/empresa/cambiar/", False),
        ("POST", "/api/v1/auth/login/", False),
    ],
)
def test_whitelist_paths(method, path, expected):
    assert is_auth_route_whitelisted(method, path) is expected


@pytest.mark.unit
def test_exclusions_impersonation_and_sso():
    usuario = _usuario(requiere_cambio=True, proveedor="local")
    assert is_excluded_from_password_change_enforcement(
        payload={"is_impersonation": True},
        usuario=usuario,
    )
    assert is_excluded_from_password_change_enforcement(
        payload={"user_type": "platform_admin", "es_superadmin": True},
        usuario=usuario,
    )
    usuario_sso = _usuario(requiere_cambio=True, proveedor="azure_ad")
    assert is_excluded_from_password_change_enforcement(
        payload={},
        usuario=usuario_sso,
    )


@pytest.mark.unit
def test_enforcement_blocks_erp_route():
    usuario = _usuario(requiere_cambio=True)
    payload = {"sub": "admin", "user_type": "tenant_admin"}
    req = _request("GET", "/api/v1/inv/productos/")
    with pytest.raises(AuthorizationError) as exc:
        enforce_password_change_policy(
            request=req,
            payload=payload,
            usuario=usuario,
        )
    assert exc.value.status_code == 403
    assert exc.value.internal_code == PASSWORD_CHANGE_REQUIRED_CODE


@pytest.mark.unit
def test_enforcement_allows_me_whitelist():
    usuario = _usuario(requiere_cambio=True)
    payload = {"sub": "admin", "user_type": "tenant_admin"}
    req = _request("GET", "/api/v1/auth/me/")
    enforce_password_change_policy(
        request=req,
        payload=payload,
        usuario=usuario,
    )


@pytest.mark.unit
def test_resolve_requires_password_change_bit_and_bool():
    assert (
        AuthService.resolve_requires_password_change({"requiere_cambio_contrasena": 1})
        is True
    )
    assert (
        AuthService.resolve_requires_password_change({"requiere_cambio_contrasena": 0})
        is False
    )
    assert (
        AuthService.resolve_requires_password_change({"requiere_cambio_contrasena": True})
        is True
    )
    assert AuthService.resolve_requires_password_change({}) is False


@pytest.mark.unit
def test_build_token_data_includes_requires_password_change_from_bd_not_claim():
    token_data = AuthService.build_token_data_from_level_info(
        username="admin",
        cliente_id=uuid4(),
        level_info={"access_level": 4, "is_super_admin": False, "user_type": "tenant_admin"},
        refresh_payload={"requires_password_change": True},
        requires_password_change=False,
    )
    assert token_data["requires_password_change"] is False


@pytest.mark.unit
def test_user_data_schema_requires_password_change_field():
    profile = build_user_data_with_roles_dict(
        usuario_id=uuid4(),
        nombre_usuario="admin",
        correo="a@b.com",
        nombre="Admin",
        apellido=None,
        es_activo=True,
        roles=["Administrador"],
        access_level=4,
        is_super_admin=False,
        user_type="tenant_admin",
        cliente_id=uuid4(),
        es_admin_cliente=True,
        requires_password_change=True,
    )
    user_data = UserDataWithRoles.model_validate(profile)
    assert user_data.requires_password_change is True


@pytest.mark.unit
def test_password_change_request_validates_strength():
    with pytest.raises(ValueError):
        PasswordChangeRequest(current_password="old", new_password="short")


@pytest.mark.unit
def test_resolve_from_user_object():
    usuario = _usuario(requiere_cambio=True)
    assert resolve_requires_password_change_from_user(usuario) is True
