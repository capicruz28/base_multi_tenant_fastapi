"""
Hybrid Dedicated Mock Harness — metadata factory (PR-F0-01).

Capa pura sin pytest ni I/O. Shape alineado con routing.py (cliente_conexion).
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from app.core.tenant.context import TenantContext
from app.infrastructure.database.connection_async import DatabaseConnection

# UUID determinísticos — namespace distinto de IAM V2 (aaaa/bbbb)
HYBRID_FIXTURE_TENANT_SHARED = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
HYBRID_FIXTURE_TENANT_DEDICATED = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")

_MOCK_DEDICATED_SERVER = "mock-dedicated.local"
_MOCK_DEDICATED_DB = "bd_hybrid_mock_dedicated"
_MOCK_SHARED_DB = "bd_hybrid_mock_shared"
_MOCK_USER = "hybrid_mock_user"
_MOCK_PASSWORD = "hybrid_mock_password"


def build_shared_metadata(client_id: UUID) -> Dict[str, Any]:
    """Metadata AS-IS shared → database_type single."""
    return {
        "database_type": "single",
        "servidor": None,
        "puerto": 1433,
        "nombre_bd": _MOCK_SHARED_DB,
        "usuario": "",
        "password": "",
        "tipo_bd": "sqlserver",
        "usa_ssl": False,
        "tipo_instalacion": "shared",
        "metadata_json": {},
    }


def build_dedicated_metadata(client_id: UUID) -> Dict[str, Any]:
    """Metadata AS-IS dedicated → database_type multi + Storage Endpoint."""
    return {
        "database_type": "multi",
        "servidor": _MOCK_DEDICATED_SERVER,
        "puerto": 1433,
        "nombre_bd": _MOCK_DEDICATED_DB,
        "usuario": _MOCK_USER,
        "password": _MOCK_PASSWORD,
        "tipo_bd": "sqlserver",
        "usa_ssl": False,
        "tipo_instalacion": "dedicated",
        "metadata_json": {},
    }


def resolve_engine_key(
    client_id: Optional[UUID],
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
) -> str:
    """
    Replica la regla de engine_key de connection_async._get_async_engine.

    ADMIN → "admin"
    DEFAULT + client_id → "tenant_{client_id}"

    No replica el fallback de producción cuando client_id es None
    (get_current_client_id() desde ContextVar). PR-F0-01 exige client_id
    explícito para mantener el harness determinístico sin dependencia de
    contexto de request.
    """
    if connection_type == DatabaseConnection.ADMIN:
        return "admin"
    if client_id is None:
        raise ValueError("client_id es obligatorio para resolver engine key tenant_*")
    return f"tenant_{client_id}"


def build_tenant_context(
    client_id: UUID,
    metadata: Dict[str, Any],
    *,
    subdominio: str,
    codigo_cliente: str,
) -> TenantContext:
    """Construye TenantContext de producción a partir de metadata mock."""
    return TenantContext(
        client_id=client_id,
        subdominio=subdominio,
        codigo_cliente=codigo_cliente,
        database_type=metadata.get("database_type", "single"),
        nombre_bd=metadata.get("nombre_bd"),
        connection_metadata=metadata,
        servidor=metadata.get("servidor"),
        puerto=metadata.get("puerto"),
        tipo_instalacion=metadata.get("tipo_instalacion"),
    )
