"""
Queries SQLAlchemy Core para wms_tarea.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import WmsTareaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in WmsTareaTable.c}


async def list_tareas(
    client_id: UUID,
    almacen_id: Optional[UUID] = None,
    tipo_tarea: Optional[str] = None,
    estado: Optional[str] = None,
    asignado_usuario_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista tareas de almacén del tenant. Siempre filtra por cliente_id."""
    query = select(WmsTareaTable).where(
        WmsTareaTable.c.cliente_id == client_id
    )
    if almacen_id:
        query = query.where(WmsTareaTable.c.almacen_id == almacen_id)
    if tipo_tarea:
        query = query.where(WmsTareaTable.c.tipo_tarea == tipo_tarea)
    if estado:
        query = query.where(WmsTareaTable.c.estado == estado)
    if asignado_usuario_id:
        query = query.where(WmsTareaTable.c.asignado_usuario_id == asignado_usuario_id)
    if producto_id:
        query = query.where(WmsTareaTable.c.producto_id == producto_id)
    if buscar:
        search_filter = or_(
            WmsTareaTable.c.numero_tarea.ilike(f"%{buscar}%"),
            WmsTareaTable.c.instrucciones.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(WmsTareaTable.c.prioridad, WmsTareaTable.c.fecha_creacion.desc())
    return await execute_query(query, client_id=client_id)


async def get_tarea_by_id(client_id: UUID, tarea_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una tarea por id. Exige cliente_id para no cruzar tenants."""
    query = select(WmsTareaTable).where(
        and_(
            WmsTareaTable.c.cliente_id == client_id,
            WmsTareaTable.c.tarea_id == tarea_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_tarea(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una tarea. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("tarea_id", uuid4())
    stmt = insert(WmsTareaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_tarea_by_id(client_id, payload["tarea_id"])


async def update_tarea(
    client_id: UUID, tarea_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una tarea. WHERE incluye cliente_id y tarea_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("tarea_id", "cliente_id")
    }
    if not payload:
        return await get_tarea_by_id(client_id, tarea_id)
    stmt = (
        update(WmsTareaTable)
        .where(
            and_(
                WmsTareaTable.c.cliente_id == client_id,
                WmsTareaTable.c.tarea_id == tarea_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_tarea_by_id(client_id, tarea_id)
