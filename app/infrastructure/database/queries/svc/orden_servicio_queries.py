"""Queries para svc_orden_servicio. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import SvcOrdenServicioTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in SvcOrdenServicioTable.c}


async def list_orden_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    cliente_venta_id: Optional[UUID] = None,
    tipo_servicio: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(SvcOrdenServicioTable).where(
        SvcOrdenServicioTable.c.cliente_id == client_id
    )
    if empresa_id:
        q = q.where(SvcOrdenServicioTable.c.empresa_id == empresa_id)
    if estado:
        q = q.where(SvcOrdenServicioTable.c.estado == estado)
    if cliente_venta_id:
        q = q.where(SvcOrdenServicioTable.c.cliente_venta_id == cliente_venta_id)
    if tipo_servicio:
        q = q.where(SvcOrdenServicioTable.c.tipo_servicio == tipo_servicio)
    if buscar:
        q = q.where(or_(
            SvcOrdenServicioTable.c.numero_os.ilike(f"%{buscar}%"),
            SvcOrdenServicioTable.c.descripcion_servicio.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(SvcOrdenServicioTable.c.fecha_solicitud.desc(), SvcOrdenServicioTable.c.numero_os)
    return await execute_query(q, client_id=client_id)


async def get_orden_servicio_by_id(
    client_id: UUID, orden_servicio_id: UUID
) -> Optional[Dict[str, Any]]:
    q = select(SvcOrdenServicioTable).where(
        and_(
            SvcOrdenServicioTable.c.cliente_id == client_id,
            SvcOrdenServicioTable.c.orden_servicio_id == orden_servicio_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_orden_servicio(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("orden_servicio_id", uuid4())
    await execute_insert(insert(SvcOrdenServicioTable).values(**payload), client_id=client_id)
    return await get_orden_servicio_by_id(client_id, payload["orden_servicio_id"])


async def update_orden_servicio(
    client_id: UUID, orden_servicio_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("orden_servicio_id", "cliente_id")
    }
    if not payload:
        return await get_orden_servicio_by_id(client_id, orden_servicio_id)
    stmt = update(SvcOrdenServicioTable).where(
        and_(
            SvcOrdenServicioTable.c.cliente_id == client_id,
            SvcOrdenServicioTable.c.orden_servicio_id == orden_servicio_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_orden_servicio_by_id(client_id, orden_servicio_id)
