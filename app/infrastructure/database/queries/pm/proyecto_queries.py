"""Queries para pm_proyecto. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import PmProyectoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PmProyectoTable.c}


async def list_proyecto(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    cliente_venta_id: Optional[UUID] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(PmProyectoTable).where(PmProyectoTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(PmProyectoTable.c.empresa_id == empresa_id)
    if estado:
        q = q.where(PmProyectoTable.c.estado == estado)
    if cliente_venta_id:
        q = q.where(PmProyectoTable.c.cliente_venta_id == cliente_venta_id)
    if buscar:
        q = q.where(or_(
            PmProyectoTable.c.nombre.ilike(f"%{buscar}%"),
            PmProyectoTable.c.codigo_proyecto.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(PmProyectoTable.c.fecha_inicio.desc(), PmProyectoTable.c.codigo_proyecto)
    return await execute_query(q, client_id=client_id)


async def get_proyecto_by_id(client_id: UUID, proyecto_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(PmProyectoTable).where(
        and_(
            PmProyectoTable.c.cliente_id == client_id,
            PmProyectoTable.c.proyecto_id == proyecto_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_proyecto(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("proyecto_id", uuid4())
    await execute_insert(insert(PmProyectoTable).values(**payload), client_id=client_id)
    return await get_proyecto_by_id(client_id, payload["proyecto_id"])


async def update_proyecto(
    client_id: UUID, proyecto_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("proyecto_id", "cliente_id")
    }
    if not payload:
        return await get_proyecto_by_id(client_id, proyecto_id)
    stmt = update(PmProyectoTable).where(
        and_(
            PmProyectoTable.c.cliente_id == client_id,
            PmProyectoTable.c.proyecto_id == proyecto_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_proyecto_by_id(client_id, proyecto_id)
