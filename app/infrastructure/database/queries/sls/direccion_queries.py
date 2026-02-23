"""
Queries SQLAlchemy Core para sls_cliente_direccion.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import SlsClienteDireccionTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in SlsClienteDireccionTable.c}


async def list_direcciones(
    client_id: UUID,
    cliente_venta_id: Optional[UUID] = None,
    solo_activos: bool = True
) -> List[Dict[str, Any]]:
    """Lista direcciones del tenant. Siempre filtra por cliente_id."""
    query = select(SlsClienteDireccionTable).where(
        SlsClienteDireccionTable.c.cliente_id == client_id
    )
    if cliente_venta_id:
        query = query.where(SlsClienteDireccionTable.c.cliente_venta_id == cliente_venta_id)
    if solo_activos:
        query = query.where(SlsClienteDireccionTable.c.es_activo == True)
    query = query.order_by(SlsClienteDireccionTable.c.nombre_direccion)
    return await execute_query(query, client_id=client_id)


async def get_direccion_by_id(client_id: UUID, direccion_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una direccion por id. Exige cliente_id para no cruzar tenants."""
    query = select(SlsClienteDireccionTable).where(
        and_(
            SlsClienteDireccionTable.c.cliente_id == client_id,
            SlsClienteDireccionTable.c.direccion_id == direccion_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_direccion(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una direccion. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("direccion_id", uuid4())
    stmt = insert(SlsClienteDireccionTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_direccion_by_id(client_id, payload["direccion_id"])


async def update_direccion(
    client_id: UUID, direccion_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una direccion. WHERE incluye cliente_id y direccion_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("direccion_id", "cliente_id")
    }
    if not payload:
        return await get_direccion_by_id(client_id, direccion_id)
    stmt = (
        update(SlsClienteDireccionTable)
        .where(
            and_(
                SlsClienteDireccionTable.c.cliente_id == client_id,
                SlsClienteDireccionTable.c.direccion_id == direccion_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_direccion_by_id(client_id, direccion_id)
