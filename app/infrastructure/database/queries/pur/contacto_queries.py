"""
Queries SQLAlchemy Core para pur_proveedor_contacto.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PurProveedorContactoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PurProveedorContactoTable.c}


async def list_contactos(
    client_id: UUID,
    proveedor_id: Optional[UUID] = None,
    solo_activos: bool = True
) -> List[Dict[str, Any]]:
    """Lista contactos del tenant. Siempre filtra por cliente_id."""
    query = select(PurProveedorContactoTable).where(
        PurProveedorContactoTable.c.cliente_id == client_id
    )
    if proveedor_id:
        query = query.where(PurProveedorContactoTable.c.proveedor_id == proveedor_id)
    if solo_activos:
        query = query.where(PurProveedorContactoTable.c.es_activo == True)
    query = query.order_by(PurProveedorContactoTable.c.nombre_completo)
    return await execute_query(query, client_id=client_id)


async def get_contacto_by_id(client_id: UUID, contacto_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un contacto por id. Exige cliente_id para no cruzar tenants."""
    query = select(PurProveedorContactoTable).where(
        and_(
            PurProveedorContactoTable.c.cliente_id == client_id,
            PurProveedorContactoTable.c.contacto_id == contacto_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_contacto(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un contacto. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("contacto_id", uuid4())
    stmt = insert(PurProveedorContactoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_contacto_by_id(client_id, payload["contacto_id"])


async def update_contacto(
    client_id: UUID, contacto_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un contacto. WHERE incluye cliente_id y contacto_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("contacto_id", "cliente_id")
    }
    if not payload:
        return await get_contacto_by_id(client_id, contacto_id)
    stmt = (
        update(PurProveedorContactoTable)
        .where(
            and_(
                PurProveedorContactoTable.c.cliente_id == client_id,
                PurProveedorContactoTable.c.contacto_id == contacto_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_contacto_by_id(client_id, contacto_id)
