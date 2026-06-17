"""
Enforcement centralizado — FORCE PASSWORD CHANGE (estrategia O5).

Punto de inyección: get_current_active_user (app/api/deps.py).
Whitelist explícita de rutas auth; el resto del ERP queda bloqueado con 403.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from fastapi import Request

from app.core.config import settings
from app.core.exceptions import AuthorizationError

PASSWORD_CHANGE_REQUIRED_CODE = "PASSWORD_CHANGE_REQUIRED"

_API_PREFIX = settings.API_V1_STR.rstrip("/")

# Rutas exactas (method, path normalizado)
_EXACT_WHITELIST: frozenset[tuple[str, str]] = frozenset(
    {
        ("POST", f"{_API_PREFIX}/auth/password/change/"),
        ("POST", f"{_API_PREFIX}/auth/password/change"),
        ("GET", f"{_API_PREFIX}/auth/me/"),
        ("GET", f"{_API_PREFIX}/auth/me"),
        ("POST", f"{_API_PREFIX}/auth/logout/"),
        ("POST", f"{_API_PREFIX}/auth/logout"),
        ("POST", f"{_API_PREFIX}/auth/refresh/"),
        ("POST", f"{_API_PREFIX}/auth/refresh"),
        ("POST", f"{_API_PREFIX}/auth/empresa/seleccionar/"),
        ("POST", f"{_API_PREFIX}/auth/empresa/seleccionar"),
    }
)

_IMPERSONATE_PREFIX = f"{_API_PREFIX}/auth/impersonate/"


def normalize_request_path(path: str) -> str:
    """Normaliza path para matching de whitelist."""
    text = (path or "").strip()
    text = re.sub(r"/+", "/", text)
    return text


def is_auth_route_whitelisted(method: str, path: str) -> bool:
    """True si la ruta está en la whitelist mínima obligatoria."""
    norm = normalize_request_path(path)
    m = (method or "").upper()
    if (m, norm) in _EXACT_WHITELIST:
        return True
    if m == "POST" and norm.startswith(_IMPERSONATE_PREFIX):
        return True
    return False


def is_excluded_from_password_change_enforcement(
    *,
    payload: Dict[str, Any],
    usuario: Any,
    impersonation_tenant_session: bool = False,
) -> bool:
    """
    Exclusiones obligatorias: impersonación, platform_admin, superadmin, SSO.
    """
    if impersonation_tenant_session or payload.get("is_impersonation"):
        return True

    if payload.get("es_superadmin") or payload.get("is_super_admin"):
        return True

    user_type = (
        payload.get("user_type")
        or getattr(usuario, "user_type", None)
        or ""
    )
    if str(user_type).lower() == "platform_admin":
        return True

    if getattr(usuario, "is_super_admin", False):
        username = getattr(usuario, "nombre_usuario", None) or payload.get("sub")
        if username == settings.SUPERADMIN_USERNAME:
            return True
        if str(user_type).lower() in ("platform_admin", "super_admin"):
            return True

    proveedor = (
        getattr(usuario, "proveedor_autenticacion", None)
        or payload.get("proveedor_autenticacion")
        or "local"
    )
    if str(proveedor).strip().lower() != "local":
        return True

    return False


def resolve_requires_password_change_from_user(usuario: Any) -> bool:
    """Lee flag desde objeto usuario (fuente BD vía build_user_with_roles)."""
    val = getattr(usuario, "requiere_cambio_contrasena", None)
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return val != 0
    return bool(val)


def enforce_password_change_policy(
    *,
    request: Request,
    payload: Dict[str, Any],
    usuario: Any,
    impersonation_tenant_session: bool = False,
) -> None:
    """
    Bloquea acceso ERP si el usuario local requiere cambio de contraseña.
    Lanza AuthorizationError (403, PASSWORD_CHANGE_REQUIRED).
    """
    if is_excluded_from_password_change_enforcement(
        payload=payload,
        usuario=usuario,
        impersonation_tenant_session=impersonation_tenant_session,
    ):
        return

    if not resolve_requires_password_change_from_user(usuario):
        return

    if is_auth_route_whitelisted(request.method, request.url.path):
        return

    raise AuthorizationError(
        detail="Debe cambiar su contraseña antes de acceder a este recurso.",
        internal_code=PASSWORD_CHANGE_REQUIRED_CODE,
    )
