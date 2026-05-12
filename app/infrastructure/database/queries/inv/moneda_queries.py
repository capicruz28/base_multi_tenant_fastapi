"""
Queries de soporte para moneda (cat_moneda) usadas por INV.

Nota: cat_moneda es un catálogo global (sin cliente_id), pero la conexión
se resuelve por tenant (client_id) en execute_query.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select

from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.tables_erp import CatMonedaTable


async def get_moneda_by_codigo(
    *,
    client_id: UUID,
    codigo: str,
    solo_activos: bool = True,
) -> Optional[Dict[str, Any]]:
    codigo_u = (codigo or "").strip().upper()
    if not codigo_u:
        return None
    q = select(CatMonedaTable).where(CatMonedaTable.c.codigo == codigo_u)
    if solo_activos:
        q = q.where(CatMonedaTable.c.es_activo == True)  # noqa: E712
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None

