"""
Queries SQLAlchemy Core para qms_inspeccion y qms_inspeccion_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import (
    QmsInspeccionTable,
    QmsInspeccionDetalleTable,
)
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS_INSP = {c.name for c in QmsInspeccionTable.c}
_COLUMNS_DETALLE = {c.name for c in QmsInspeccionDetalleTable.c}


async def list_inspecciones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    plan_inspeccion_id: Optional[UUID] = None,
    resultado: Optional[str] = None,
    lote: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista inspecciones del tenant."""
    query = select(QmsInspeccionTable).where(
        QmsInspeccionTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(QmsInspeccionTable.c.empresa_id == empresa_id)
    if producto_id:
        query = query.where(QmsInspeccionTable.c.producto_id == producto_id)
    if plan_inspeccion_id:
        query = query.where(QmsInspeccionTable.c.plan_inspeccion_id == plan_inspeccion_id)
    if resultado:
        query = query.where(QmsInspeccionTable.c.resultado == resultado)
    if lote:
        query = query.where(QmsInspeccionTable.c.lote == lote)
    if fecha_desde:
        query = query.where(QmsInspeccionTable.c.fecha_inspeccion >= fecha_desde)
    if fecha_hasta:
        query = query.where(QmsInspeccionTable.c.fecha_inspeccion <= fecha_hasta)
    if buscar:
        search_filter = or_(
            QmsInspeccionTable.c.numero_inspeccion.ilike(f"%{buscar}%"),
            QmsInspeccionTable.c.observaciones.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(QmsInspeccionTable.c.fecha_inspeccion.desc())
    return await execute_query(query, client_id=client_id)


async def get_inspeccion_by_id(client_id: UUID, inspeccion_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una inspección por id."""
    query = select(QmsInspeccionTable).where(
        and_(
            QmsInspeccionTable.c.cliente_id == client_id,
            QmsInspeccionTable.c.inspeccion_id == inspeccion_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_inspeccion(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una inspección."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS_INSP}
    payload["cliente_id"] = client_id
    payload.setdefault("inspeccion_id", uuid4())
    stmt = insert(QmsInspeccionTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_inspeccion_by_id(client_id, payload["inspeccion_id"])


async def update_inspeccion(
    client_id: UUID, inspeccion_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una inspección."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS_INSP and k not in ("inspeccion_id", "cliente_id")
    }
    if not payload:
        return await get_inspeccion_by_id(client_id, inspeccion_id)
    stmt = (
        update(QmsInspeccionTable)
        .where(
            and_(
                QmsInspeccionTable.c.cliente_id == client_id,
                QmsInspeccionTable.c.inspeccion_id == inspeccion_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_inspeccion_by_id(client_id, inspeccion_id)


async def list_inspeccion_detalles(
    client_id: UUID, inspeccion_id: UUID
) -> List[Dict[str, Any]]:
    """Lista detalles de una inspección."""
    query = select(QmsInspeccionDetalleTable).where(
        and_(
            QmsInspeccionDetalleTable.c.cliente_id == client_id,
            QmsInspeccionDetalleTable.c.inspeccion_id == inspeccion_id,
        )
    )
    return await execute_query(query, client_id=client_id)


async def get_inspeccion_detalle_by_id(
    client_id: UUID, inspeccion_detalle_id: UUID
) -> Optional[Dict[str, Any]]:
    """Obtiene un detalle por id."""
    query = select(QmsInspeccionDetalleTable).where(
        and_(
            QmsInspeccionDetalleTable.c.cliente_id == client_id,
            QmsInspeccionDetalleTable.c.inspeccion_detalle_id == inspeccion_detalle_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_inspeccion_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un detalle de inspección."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS_DETALLE}
    payload["cliente_id"] = client_id
    payload.setdefault("inspeccion_detalle_id", uuid4())
    stmt = insert(QmsInspeccionDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_inspeccion_detalle_by_id(client_id, payload["inspeccion_detalle_id"])


async def update_inspeccion_detalle(
    client_id: UUID, inspeccion_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un detalle de inspección."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS_DETALLE and k not in ("inspeccion_detalle_id", "cliente_id")
    }
    if not payload:
        return await get_inspeccion_detalle_by_id(client_id, inspeccion_detalle_id)
    stmt = (
        update(QmsInspeccionDetalleTable)
        .where(
            and_(
                QmsInspeccionDetalleTable.c.cliente_id == client_id,
                QmsInspeccionDetalleTable.c.inspeccion_detalle_id == inspeccion_detalle_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_inspeccion_detalle_by_id(client_id, inspeccion_detalle_id)
