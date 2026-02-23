"""
Queries SQLAlchemy Core para inv_almacen.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import InvAlmacenTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in InvAlmacenTable.c}


async def list_almacenes(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    sucursal_id: Optional[UUID] = None,
    solo_activos: bool = True
) -> List[Dict[str, Any]]:
    """Lista almacenes del tenant. Siempre filtra por cliente_id."""
    query = select(InvAlmacenTable).where(
        InvAlmacenTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(InvAlmacenTable.c.empresa_id == empresa_id)
    if sucursal_id:
        query = query.where(InvAlmacenTable.c.sucursal_id == sucursal_id)
    if solo_activos:
        query = query.where(InvAlmacenTable.c.es_activo == True)
    query = query.order_by(InvAlmacenTable.c.nombre)
    return await execute_query(query, client_id=client_id)


async def get_almacen_by_id(client_id: UUID, almacen_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un almacén por id. Exige cliente_id para no cruzar tenants."""
    query = select(InvAlmacenTable).where(
        and_(
            InvAlmacenTable.c.cliente_id == client_id,
            InvAlmacenTable.c.almacen_id == almacen_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_almacen(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un almacén. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("almacen_id", uuid4())
    stmt = insert(InvAlmacenTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_almacen_by_id(client_id, payload["almacen_id"])


async def update_almacen(
    client_id: UUID, almacen_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un almacén. WHERE incluye cliente_id y almacen_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("almacen_id", "cliente_id")
    }
    if not payload:
        return await get_almacen_by_id(client_id, almacen_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(InvAlmacenTable)
        .where(
            and_(
                InvAlmacenTable.c.cliente_id == client_id,
                InvAlmacenTable.c.almacen_id == almacen_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_almacen_by_id(client_id, almacen_id)
