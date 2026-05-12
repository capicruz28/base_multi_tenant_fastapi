"""
Queries SQLAlchemy Core para pur_recepcion_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PurRecepcionDetalleTable
from app.infrastructure.database.queries_async import (
    execute_query,
    execute_insert,
    execute_update,
)

_COLUMNS = {c.name for c in PurRecepcionDetalleTable.c}
_COMPUTED = frozenset({"diferencia", "total"})
_WRITABLE_COLUMNS = _COLUMNS - _COMPUTED


async def list_recepciones_detalle(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    recepcion_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Lista líneas de recepción del tenant. Siempre filtra por cliente_id."""
    query = select(PurRecepcionDetalleTable).where(
        PurRecepcionDetalleTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(PurRecepcionDetalleTable.c.empresa_id == empresa_id)
    if recepcion_id:
        query = query.where(
            PurRecepcionDetalleTable.c.recepcion_id == recepcion_id
        )
    if producto_id:
        query = query.where(PurRecepcionDetalleTable.c.producto_id == producto_id)
    query = query.order_by(
        PurRecepcionDetalleTable.c.recepcion_id,
        PurRecepcionDetalleTable.c.producto_id,
    )
    return await execute_query(query, client_id=client_id)


async def get_recepcion_detalle_by_id(
    client_id: UUID, recepcion_detalle_id: UUID
) -> Optional[Dict[str, Any]]:
    """Obtiene una línea de recepción por id. Exige cliente_id para no cruzar tenants."""
    query = select(PurRecepcionDetalleTable).where(
        and_(
            PurRecepcionDetalleTable.c.cliente_id == client_id,
            PurRecepcionDetalleTable.c.recepcion_detalle_id == recepcion_detalle_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_recepcion_detalle(
    client_id: UUID, data: Dict[str, Any]
) -> Dict[str, Any]:
    """Inserta una línea de recepción. cliente_id se fuerza desde contexto."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _WRITABLE_COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("recepcion_detalle_id", uuid4())
    stmt = insert(PurRecepcionDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_recepcion_detalle_by_id(
        client_id, payload["recepcion_detalle_id"]
    )


async def update_recepcion_detalle(
    client_id: UUID, recepcion_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una línea de recepción. WHERE incluye cliente_id e id de detalle."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _WRITABLE_COLUMNS
        and k
        not in (
            "recepcion_detalle_id",
            "cliente_id",
        )
    }
    if not payload:
        return await get_recepcion_detalle_by_id(
            client_id, recepcion_detalle_id
        )
    stmt = (
        update(PurRecepcionDetalleTable)
        .where(
            and_(
                PurRecepcionDetalleTable.c.cliente_id == client_id,
                PurRecepcionDetalleTable.c.recepcion_detalle_id
                == recepcion_detalle_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_recepcion_detalle_by_id(
        client_id, recepcion_detalle_id
    )
