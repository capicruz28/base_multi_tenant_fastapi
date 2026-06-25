"""Whitelist única de columnas para lectura de sesiones activas (C21)."""
from __future__ import annotations

from typing import Any, Dict, List, Set

from sqlalchemy.sql.schema import Column

from app.infrastructure.database.tables import RefreshTokensTable, UserSessionTable

# V1 — columnas refresh_tokens vigentes en esquema V3 (+ enriquecimiento user_session en C09).
ACTIVE_SESSION_TOKEN_COLUMN_NAMES: tuple[str, ...] = (
    "token_id",
    "session_id",
    "usuario_id",
    "cliente_id",
    "empresa_id",
    "created_at",
    "last_used_at",
    "expires_at",
)

# V2 — columnas user_session en listados (fuente canónica sesión lógica).
ACTIVE_SESSION_V2_SESSION_COLUMN_NAMES: tuple[str, ...] = (
    "session_id",
    "usuario_id",
    "cliente_id",
    "empresa_id",
    "login_method",
    "platform",
    "device_name",
    "device_id",
    "user_agent",
    "login_ip",
    "last_seen_ip",
    "created_at",
    "last_refresh_at",
    "expires_at",
    "revoked_at",
    "revoked_reason",
)

ACTIVE_SESSION_V2_TOKEN_COLUMN_NAMES: tuple[str, ...] = (
    "token_id",
    "family_id",
)

ADMIN_SESSIONS_SORT_COLUMNS_V1: frozenset[str] = frozenset(
    {
        "created_at",
        "last_used_at",
        "expires_at",
        "ip_address",
        "device_name",
        "client_type",
        "nombre_usuario",
        "token_id",
    }
)

ADMIN_SESSIONS_SORT_COLUMNS_V2: frozenset[str] = frozenset(
    ADMIN_SESSIONS_SORT_COLUMNS_V1
    | {
        "session_id",
        "platform",
        "login_ip",
        "last_refresh_at",
        "last_seen_ip",
        "login_method",
        "family_id",
    }
)

ADMIN_SESSIONS_SEARCH_COLUMNS_V1: frozenset[str] = frozenset(
    {
        "nombre_usuario",
        "nombre",
        "apellido",
        "ip_address",
        "device_name",
    }
)

ADMIN_SESSIONS_SEARCH_COLUMNS_V2: frozenset[str] = frozenset(
    ADMIN_SESSIONS_SEARCH_COLUMNS_V1
    | {
        "login_ip",
        "last_seen_ip",
        "platform",
        "device_id",
    }
)


def active_session_token_columns() -> List[Column]:
    """Columnas refresh_tokens usadas por listado V1."""
    table = RefreshTokensTable
    return [table.c[name] for name in ACTIVE_SESSION_TOKEN_COLUMN_NAMES]


def active_session_v2_session_columns() -> List[Column]:
    """Columnas user_session para listado V2."""
    table = UserSessionTable
    return [table.c[name] for name in ACTIVE_SESSION_V2_SESSION_COLUMN_NAMES]


def admin_sessions_sort_columns(*, v2_enabled: bool) -> frozenset[str]:
    """Whitelist sort_by admin según motor de lectura."""
    return ADMIN_SESSIONS_SORT_COLUMNS_V2 if v2_enabled else ADMIN_SESSIONS_SORT_COLUMNS_V1


def admin_sessions_search_columns(*, v2_enabled: bool) -> frozenset[str]:
    """Whitelist búsqueda admin."""
    return ADMIN_SESSIONS_SEARCH_COLUMNS_V2 if v2_enabled else ADMIN_SESSIONS_SEARCH_COLUMNS_V1


def normalize_admin_sort_by(sort_by: str | None, *, v2_enabled: bool) -> str | None:
    """Alias V1 → V2 para sort (last_used_at ≡ last_refresh_at en V2)."""
    if not sort_by:
        return sort_by
    if v2_enabled and sort_by == "last_used_at":
        return "last_refresh_at"
    if v2_enabled and sort_by == "ip_address":
        return "last_seen_ip"
    if v2_enabled and sort_by == "client_type":
        return "platform"
    return sort_by


def v2_session_column_map() -> Dict[str, Any]:
    """Mapa sort/filter V2 — única whitelist C21."""
    cols = {c.name: c for c in active_session_v2_session_columns()}
    return {
        "session_id": cols["session_id"],
        "created_at": cols["created_at"],
        "last_refresh_at": cols["last_refresh_at"],
        "last_used_at": cols["last_refresh_at"],
        "expires_at": cols["expires_at"],
        "login_ip": cols["login_ip"],
        "last_seen_ip": cols["last_seen_ip"],
        "ip_address": cols["last_seen_ip"],
        "device_name": cols["device_name"],
        "platform": cols["platform"],
        "client_type": cols["platform"],
        "login_method": cols["login_method"],
    }


__all__ = [
    "ACTIVE_SESSION_TOKEN_COLUMN_NAMES",
    "ACTIVE_SESSION_V2_SESSION_COLUMN_NAMES",
    "ACTIVE_SESSION_V2_TOKEN_COLUMN_NAMES",
    "ADMIN_SESSIONS_SEARCH_COLUMNS_V1",
    "ADMIN_SESSIONS_SEARCH_COLUMNS_V2",
    "ADMIN_SESSIONS_SORT_COLUMNS_V1",
    "ADMIN_SESSIONS_SORT_COLUMNS_V2",
    "active_session_token_columns",
    "active_session_v2_session_columns",
    "admin_sessions_search_columns",
    "admin_sessions_sort_columns",
    "normalize_admin_sort_by",
    "v2_session_column_map",
]
