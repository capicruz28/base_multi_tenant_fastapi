"""Mapper único de filas refresh_tokens → DTOs de sesión activa (IAM-SESSIONS-V1)."""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from app.modules.auth.presentation.schemas_admin_sessions import AdminSessionRead
from app.modules.auth.presentation.schemas_sessions import (
    SessionDeviceRead,
    SessionStatus,
    UserSessionRead,
)

_UNKNOWN = "Desconocido"
_EXPIRING_SOON_HOURS = 24


def _parse_user_agent(user_agent: Optional[str], client_type: str) -> Dict[str, Optional[str]]:
    """Parseo fail-soft de User-Agent (funciones privadas — sin módulo separado)."""
    ua = (user_agent or "").strip()
    ct = (client_type or "web").lower()

    browser = _UNKNOWN
    browser_version: Optional[str] = None
    os_name = _UNKNOWN
    platform = "unknown"

    if not ua:
        return {
            "browser": browser,
            "browser_version": browser_version,
            "os": os_name,
            "platform": platform,
            "device_label": f"{ct} client",
        }

    ua_lower = ua.lower()

    if "android" in ua_lower:
        os_name = "Android"
        platform = "mobile"
    elif "iphone" in ua_lower or "ipad" in ua_lower or "ipod" in ua_lower:
        os_name = "iOS"
        platform = "tablet" if "ipad" in ua_lower else "mobile"
    elif "windows" in ua_lower:
        os_name = "Windows"
        platform = "desktop"
    elif "mac os x" in ua_lower or "macintosh" in ua_lower:
        os_name = "macOS"
        platform = "desktop"
    elif "linux" in ua_lower:
        os_name = "Linux"
        platform = "desktop"

    if "edg/" in ua_lower or "edge/" in ua_lower:
        browser = "Edge"
        browser_version = _extract_version(ua, r"Edg/(\d+[\.\d]*)") or _extract_version(
            ua, r"Edge/(\d+[\.\d]*)"
        )
    elif "chrome/" in ua_lower and "chromium" not in ua_lower:
        browser = "Chrome"
        browser_version = _extract_version(ua, r"Chrome/(\d+[\.\d]*)")
    elif "firefox/" in ua_lower:
        browser = "Firefox"
        browser_version = _extract_version(ua, r"Firefox/(\d+[\.\d]*)")
    elif "safari/" in ua_lower and "chrome" not in ua_lower:
        browser = "Safari"
        browser_version = _extract_version(ua, r"Version/(\d+[\.\d]*)")
    elif "okhttp" in ua_lower:
        browser = "OkHttp"
        platform = "mobile" if platform == "unknown" else platform
    elif ct == "mobile":
        browser = "Mobile App"

    if platform == "unknown":
        platform = "mobile" if ct == "mobile" else "desktop"

    version_suffix = f" {browser_version}" if browser_version else ""
    device_label = f"{browser}{version_suffix} en {os_name}"

    return {
        "browser": browser,
        "browser_version": browser_version,
        "os": os_name,
        "platform": platform,
        "device_label": device_label,
    }


def _extract_version(user_agent: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, user_agent, re.IGNORECASE)
    if not match:
        return None
    return match.group(1)


def _derive_status(expires_at: Optional[datetime], now: datetime) -> SessionStatus:
    if expires_at is None:
        return "active"
    if expires_at <= now:
        return "active"
    if expires_at - now <= timedelta(hours=_EXPIRING_SOON_HOURS):
        return "expiring_soon"
    return "active"


def _build_device(row: Dict[str, Any]) -> SessionDeviceRead:
    client_type = str(row.get("client_type") or "web")
    parsed = _parse_user_agent(row.get("user_agent"), client_type)
    device_label = parsed["device_label"]
    if row.get("device_name"):
        device_label = str(row["device_name"])

    return SessionDeviceRead(
        client_type=client_type,
        browser=parsed["browser"] or _UNKNOWN,
        browser_version=parsed["browser_version"],
        os=parsed["os"] or _UNKNOWN,
        platform=parsed["platform"] or "unknown",
        device_label=device_label,
        ip_address=row.get("ip_address"),
        device_id=row.get("device_id"),
    )


def _base_payload(
    row: Dict[str, Any],
    *,
    current_token_id: Optional[UUID],
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    now = now or datetime.utcnow()
    created_at = row.get("created_at") or now
    last_used_at = row.get("last_used_at")
    expires_at = row.get("expires_at") or now
    token_id = row.get("token_id")

    is_current = False
    if current_token_id and token_id:
        is_current = str(token_id) == str(current_token_id)

    duration = max(0, int((now - created_at).total_seconds()))

    device = _build_device(row)

    return {
        "token_id": token_id,
        "usuario_id": row.get("usuario_id"),
        "cliente_id": row.get("cliente_id"),
        "empresa_id": row.get("empresa_id"),
        "empresa_nombre": row.get("empresa_nombre"),
        "issued_at": created_at,
        "created_at": created_at,
        "last_refresh_at": last_used_at,
        "last_used_at": last_used_at,
        "expires_at": expires_at,
        "is_current": is_current,
        "status": _derive_status(expires_at, now),
        "duration_seconds": duration,
        "device": device,
        "client_type": str(row.get("client_type") or "web"),
        "ip_address": row.get("ip_address"),
        "device_name": row.get("device_name"),
        "device_id": row.get("device_id"),
    }


def map_row_to_user_session(
    row: Dict[str, Any],
    *,
    current_token_id: Optional[UUID] = None,
    now: Optional[datetime] = None,
) -> UserSessionRead:
    return UserSessionRead.model_validate(
        _base_payload(row, current_token_id=current_token_id, now=now)
    )


def map_row_to_admin_session(
    row: Dict[str, Any],
    *,
    current_token_id: Optional[UUID] = None,
    now: Optional[datetime] = None,
) -> AdminSessionRead:
    payload = _base_payload(row, current_token_id=current_token_id, now=now)
    payload.update(
        {
            "nombre_usuario": row.get("nombre_usuario"),
            "nombre": row.get("nombre"),
            "apellido": row.get("apellido"),
            "user_agent": row.get("user_agent"),
        }
    )
    return AdminSessionRead.model_validate(payload)


__all__ = [
    "map_row_to_admin_session",
    "map_row_to_user_session",
]
