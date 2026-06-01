"""
Persistencia de empresa preferida (usuario.empresa_default_id) — M1 multiempresa.
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import text

from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_update

logger = logging.getLogger(__name__)

USER_WITHOUT_COMPANY = "USER_WITHOUT_COMPANY"


async def persist_usuario_empresa_default_id(
    usuario_id: UUID,
    cliente_id: UUID,
    empresa_id: UUID,
) -> None:
    """R-LOGIN-07 / R-CAMBIO-03: empresa seleccionada o cambiada → preferida."""
    from app.core.tenant.context import try_get_tenant_context

    tenant_context = try_get_tenant_context()
    database_type = tenant_context.database_type if tenant_context else "single"

    if database_type == "multi":
        sql = text("""
            UPDATE usuario
            SET empresa_default_id = :empresa_id
            WHERE usuario_id = :usuario_id
              AND es_eliminado = 0
        """).bindparams(
            empresa_id=empresa_id,
            usuario_id=usuario_id,
        )
    else:
        sql = text("""
            UPDATE usuario
            SET empresa_default_id = :empresa_id
            WHERE usuario_id = :usuario_id
              AND cliente_id = :cliente_id
              AND es_eliminado = 0
        """).bindparams(
            empresa_id=empresa_id,
            usuario_id=usuario_id,
            cliente_id=cliente_id,
        )

    await execute_update(
        sql,
        connection_type=DatabaseConnection.DEFAULT,
        client_id=cliente_id,
    )
    logger.info(
        "[EMPRESA_PREF] empresa_default_id=%s usuario=%s cliente=%s",
        empresa_id,
        usuario_id,
        cliente_id,
    )


async def clear_usuario_empresa_default_id(
    usuario_id: UUID,
    cliente_id: UUID,
) -> None:
    """R-DATA-02: limpiar preferida inválida."""
    from app.core.tenant.context import try_get_tenant_context

    tenant_context = try_get_tenant_context()
    database_type = tenant_context.database_type if tenant_context else "single"

    if database_type == "multi":
        sql = text("""
            UPDATE usuario
            SET empresa_default_id = NULL
            WHERE usuario_id = :usuario_id
              AND es_eliminado = 0
        """).bindparams(usuario_id=usuario_id)
    else:
        sql = text("""
            UPDATE usuario
            SET empresa_default_id = NULL
            WHERE usuario_id = :usuario_id
              AND cliente_id = :cliente_id
              AND es_eliminado = 0
        """).bindparams(usuario_id=usuario_id, cliente_id=cliente_id)

    await execute_update(
        sql,
        connection_type=DatabaseConnection.DEFAULT,
        client_id=cliente_id,
    )
    logger.info(
        "[EMPRESA_PREF] empresa_default_id limpiada usuario=%s cliente=%s",
        usuario_id,
        cliente_id,
    )
