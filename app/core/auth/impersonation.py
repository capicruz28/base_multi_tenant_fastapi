"""
Utilidades de sesión de impersonación (soporte plataforma).

Claims oficiales: is_impersonation, impersonated_by, impersonated_by_username.
TTL fijo: IMPERSONATION_ACCESS_TTL_MINUTES (sin refresh token).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.config import settings

logger = logging.getLogger(__name__)

IMPERSONATION_ACCESS_TTL_MINUTES = 120
IMPERSONATION_REDIS_PREFIX = "impersonation:parent:"


def is_impersonation_payload(payload: Optional[Dict[str, Any]]) -> bool:
    """True si el JWT representa una sesión de impersonación activa."""
    if not payload:
        return False
    return bool(payload.get("is_impersonation"))


def impersonation_effective_level_info() -> Dict[str, Any]:
    """
    Claims LBAC del token impersonado: contexto tenant, sin privilegios platform.

    La identidad real del operador vive solo en impersonated_by / impersonated_by_username.
    """
    return {
        "access_level": 4,
        "is_super_admin": False,
        "user_type": "tenant_admin",
        "effective_scope": "tenant",
    }


def suppress_platform_privileges(
    *,
    payload: Optional[Dict[str, Any]] = None,
    is_super_admin: bool = False,
    user_type: Optional[str] = None,
    access_level: Optional[int] = None,
) -> tuple[bool, str, int]:
    """
    Durante impersonación, nunca aplicar bypass platform en menú/permisos/RBAC.
    """
    if is_impersonation_payload(payload):
        info = impersonation_effective_level_info()
        return (
            bool(info["is_super_admin"]),
            str(info["user_type"]),
            int(info["access_level"]),
        )
    return (
        is_super_admin,
        str(user_type or (payload or {}).get("user_type") or "user"),
        int(access_level if access_level is not None else (payload or {}).get("access_level") or 1),
    )


def extract_impersonation_claims(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae claims de impersonación para propagar a nuevos tokens."""
    claims: Dict[str, Any] = {"is_impersonation": True}
    operator_id = payload.get("impersonated_by")
    if operator_id is not None:
        claims["impersonated_by"] = str(operator_id)
    username = payload.get("impersonated_by_username")
    if username:
        claims["impersonated_by_username"] = str(username)
    return claims


def merge_impersonation_into_token_data(
    token_data: Dict[str, Any],
    impersonation_claims: Dict[str, Any],
) -> Dict[str, Any]:
    """Fusiona claims de impersonación en el dict base del JWT."""
    merged = {**token_data, **impersonation_claims}
    return merged


async def store_parent_session(
    impersonation_jti: str,
    *,
    parent_access_token: str,
    parent_refresh_token: Optional[str] = None,
    ttl_seconds: int,
) -> bool:
    """Guarda la sesión del operador para restaurarla al finalizar impersonación."""
    from app.infrastructure.redis.client import RedisService

    payload = {
        "parent_access_token": parent_access_token,
        "parent_refresh_token": parent_refresh_token,
    }
    return await RedisService.set_json(
        f"{IMPERSONATION_REDIS_PREFIX}{impersonation_jti}",
        payload,
        ttl_seconds,
    )


async def pop_parent_session(impersonation_jti: str) -> Optional[Dict[str, Any]]:
    """Obtiene y elimina la sesión padre asociada al jti de impersonación."""
    from app.infrastructure.redis.client import RedisService

    key = f"{IMPERSONATION_REDIS_PREFIX}{impersonation_jti}"
    data = await RedisService.get_json(key)
    if data:
        await RedisService.delete_key(key)
    return data


def impersonation_ttl_seconds() -> int:
    return IMPERSONATION_ACCESS_TTL_MINUTES * 60
