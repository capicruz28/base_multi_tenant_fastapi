"""
Queries SQLAlchemy Core para pos_punto_venta.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import PosPuntoVentaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PosPuntoVentaTable.c}


async def list_puntos_venta(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    sucursal_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista puntos de venta del tenant."""
    query = select(PosPuntoVentaTable).where(
        PosPuntoVentaTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(PosPuntoVentaTable.c.empresa_id == empresa_id)
    if sucursal_id:
        query = query.where(PosPuntoVentaTable.c.sucursal_id == sucursal_id)
    if estado:
        query = query.where(PosPuntoVentaTable.c.estado == estado)
    if es_activo is not None:
        query = query.where(PosPuntoVentaTable.c.es_activo == es_activo)
    if buscar:
        search_filter = or_(
            PosPuntoVentaTable.c.nombre.ilike(f"%{buscar}%"),
            PosPuntoVentaTable.c.codigo_punto_venta.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(PosPuntoVentaTable.c.codigo_punto_venta)
    return await execute_query(query, client_id=client_id)


async def get_punto_venta_by_id(client_id: UUID, punto_venta_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un punto de venta por id."""
    query = select(PosPuntoVentaTable).where(
        and_(
            PosPuntoVentaTable.c.cliente_id == client_id,
            PosPuntoVentaTable.c.punto_venta_id == punto_venta_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_punto_venta(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un punto de venta."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("punto_venta_id", uuid4())
    stmt = insert(PosPuntoVentaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_punto_venta_by_id(client_id, payload["punto_venta_id"])


async def update_punto_venta(
    client_id: UUID, punto_venta_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un punto de venta."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("punto_venta_id", "cliente_id")
    }
    if not payload:
        return await get_punto_venta_by_id(client_id, punto_venta_id)
    stmt = (
        update(PosPuntoVentaTable)
        .where(
            and_(
                PosPuntoVentaTable.c.cliente_id == client_id,
                PosPuntoVentaTable.c.punto_venta_id == punto_venta_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_punto_venta_by_id(client_id, punto_venta_id)
