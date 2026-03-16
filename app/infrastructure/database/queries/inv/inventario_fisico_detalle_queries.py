"""
Queries SQLAlchemy Core para inv_inventario_fisico_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import InvInventarioFisicoDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in InvInventarioFisicoDetalleTable.c}


async def list_inventarios_fisicos_detalle(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    inventario_fisico_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Lista líneas de inventarios físicos del tenant. Siempre filtra por cliente_id."""
    query = select(InvInventarioFisicoDetalleTable).where(
        InvInventarioFisicoDetalleTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(InvInventarioFisicoDetalleTable.c.empresa_id == empresa_id)
    if inventario_fisico_id:
        query = query.where(
            InvInventarioFisicoDetalleTable.c.inventario_fisico_id == inventario_fisico_id
        )
    if producto_id:
        query = query.where(InvInventarioFisicoDetalleTable.c.producto_id == producto_id)
    query = query.order_by(
        InvInventarioFisicoDetalleTable.c.inventario_fisico_id,
        InvInventarioFisicoDetalleTable.c.producto_id,
    )
    return await execute_query(query, client_id=client_id)


async def get_inventario_fisico_detalle_by_id(
    client_id: UUID, inventario_fisico_detalle_id: UUID
) -> Optional[Dict[str, Any]]:
    """Obtiene una línea de inventario físico por id. Exige cliente_id para no cruzar tenants."""
    query = select(InvInventarioFisicoDetalleTable).where(
        and_(
            InvInventarioFisicoDetalleTable.c.cliente_id == client_id,
            InvInventarioFisicoDetalleTable.c.inventario_fisico_detalle_id
            == inventario_fisico_detalle_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_inventario_fisico_detalle(
    client_id: UUID, data: Dict[str, Any]
) -> Dict[str, Any]:
    """Inserta una línea de inventario físico. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("inventario_fisico_detalle_id", uuid4())
    stmt = insert(InvInventarioFisicoDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_inventario_fisico_detalle_by_id(
        client_id, payload["inventario_fisico_detalle_id"]
    )


async def update_inventario_fisico_detalle(
    client_id: UUID, inventario_fisico_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una línea de inventario físico. WHERE incluye cliente_id e id de detalle."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS
        and k
        not in (
            "inventario_fisico_detalle_id",
            "cliente_id",
        )
    }
    if not payload:
        return await get_inventario_fisico_detalle_by_id(
            client_id, inventario_fisico_detalle_id
        )
    # No hay columna fecha_actualizacion en detalle; se deja sin timestamp adicional.
    stmt = (
        update(InvInventarioFisicoDetalleTable)
        .where(
            and_(
                InvInventarioFisicoDetalleTable.c.cliente_id == client_id,
                InvInventarioFisicoDetalleTable.c.inventario_fisico_detalle_id
                == inventario_fisico_detalle_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_inventario_fisico_detalle_by_id(
        client_id, inventario_fisico_detalle_id
    )

