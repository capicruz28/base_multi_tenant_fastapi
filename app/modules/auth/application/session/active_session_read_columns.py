"""Column set compartido para lectura de sesiones activas (IAM-SESSIONS-V1)."""
from __future__ import annotations

from typing import List

from sqlalchemy.sql.schema import Column

from app.infrastructure.database.tables import RefreshTokensTable

# Única fuente de verdad para columnas refresh_tokens en listados de sesión activa.
ACTIVE_SESSION_TOKEN_COLUMN_NAMES: tuple[str, ...] = (
    "token_id",
    "usuario_id",
    "cliente_id",
    "empresa_id",
    "created_at",
    "last_used_at",
    "expires_at",
    "device_name",
    "device_id",
    "ip_address",
    "user_agent",
    "client_type",
)


def active_session_token_columns() -> List[Column]:
    """Columnas refresh_tokens usadas por user y admin (AJUSTE GATE 4)."""
    table = RefreshTokensTable
    return [table.c[name] for name in ACTIVE_SESSION_TOKEN_COLUMN_NAMES]
