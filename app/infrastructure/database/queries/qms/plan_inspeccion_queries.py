"""
Queries SQLAlchemy Core para qms_plan_inspeccion y qms_plan_inspeccion_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import (
    QmsPlanInspeccionTable,
    QmsPlanInspeccionDetalleTable,
)
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS_PLAN = {c.name for c in QmsPlanInspeccionTable.c}
_COLUMNS_DETALLE = {c.name for c in QmsPlanInspeccionDetalleTable.c}


async def list_planes_inspeccion(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    categoria_id: Optional[UUID] = None,
    tipo_inspeccion: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista planes de inspección del tenant."""
    query = select(QmsPlanInspeccionTable).where(
        QmsPlanInspeccionTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(QmsPlanInspeccionTable.c.empresa_id == empresa_id)
    if producto_id:
        query = query.where(QmsPlanInspeccionTable.c.producto_id == producto_id)
    if categoria_id:
        query = query.where(QmsPlanInspeccionTable.c.categoria_id == categoria_id)
    if tipo_inspeccion:
        query = query.where(QmsPlanInspeccionTable.c.tipo_inspeccion == tipo_inspeccion)
    if solo_activos:
        query = query.where(QmsPlanInspeccionTable.c.es_activo == True)
    if buscar:
        search_filter = or_(
            QmsPlanInspeccionTable.c.nombre.ilike(f"%{buscar}%"),
            QmsPlanInspeccionTable.c.codigo.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(QmsPlanInspeccionTable.c.nombre)
    return await execute_query(query, client_id=client_id)


async def get_plan_inspeccion_by_id(client_id: UUID, plan_inspeccion_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un plan por id."""
    query = select(QmsPlanInspeccionTable).where(
        and_(
            QmsPlanInspeccionTable.c.cliente_id == client_id,
            QmsPlanInspeccionTable.c.plan_inspeccion_id == plan_inspeccion_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_plan_inspeccion(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un plan de inspección."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS_PLAN}
    payload["cliente_id"] = client_id
    payload.setdefault("plan_inspeccion_id", uuid4())
    stmt = insert(QmsPlanInspeccionTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_plan_inspeccion_by_id(client_id, payload["plan_inspeccion_id"])


async def update_plan_inspeccion(
    client_id: UUID, plan_inspeccion_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un plan de inspección."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS_PLAN and k not in ("plan_inspeccion_id", "cliente_id")
    }
    if not payload:
        return await get_plan_inspeccion_by_id(client_id, plan_inspeccion_id)
    stmt = (
        update(QmsPlanInspeccionTable)
        .where(
            and_(
                QmsPlanInspeccionTable.c.cliente_id == client_id,
                QmsPlanInspeccionTable.c.plan_inspeccion_id == plan_inspeccion_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_plan_inspeccion_by_id(client_id, plan_inspeccion_id)


async def list_plan_inspeccion_detalles(
    client_id: UUID, plan_inspeccion_id: UUID
) -> List[Dict[str, Any]]:
    """Lista detalles de un plan de inspección."""
    query = select(QmsPlanInspeccionDetalleTable).where(
        and_(
            QmsPlanInspeccionDetalleTable.c.cliente_id == client_id,
            QmsPlanInspeccionDetalleTable.c.plan_inspeccion_id == plan_inspeccion_id,
        )
    ).order_by(QmsPlanInspeccionDetalleTable.c.orden)
    return await execute_query(query, client_id=client_id)


async def get_plan_inspeccion_detalle_by_id(
    client_id: UUID, plan_detalle_id: UUID
) -> Optional[Dict[str, Any]]:
    """Obtiene un detalle por id."""
    query = select(QmsPlanInspeccionDetalleTable).where(
        and_(
            QmsPlanInspeccionDetalleTable.c.cliente_id == client_id,
            QmsPlanInspeccionDetalleTable.c.plan_detalle_id == plan_detalle_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_plan_inspeccion_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un detalle de plan."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS_DETALLE}
    payload["cliente_id"] = client_id
    payload.setdefault("plan_detalle_id", uuid4())
    stmt = insert(QmsPlanInspeccionDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_plan_inspeccion_detalle_by_id(client_id, payload["plan_detalle_id"])


async def update_plan_inspeccion_detalle(
    client_id: UUID, plan_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un detalle de plan."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS_DETALLE and k not in ("plan_detalle_id", "cliente_id")
    }
    if not payload:
        return await get_plan_inspeccion_detalle_by_id(client_id, plan_detalle_id)
    stmt = (
        update(QmsPlanInspeccionDetalleTable)
        .where(
            and_(
                QmsPlanInspeccionDetalleTable.c.cliente_id == client_id,
                QmsPlanInspeccionDetalleTable.c.plan_detalle_id == plan_detalle_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_plan_inspeccion_detalle_by_id(client_id, plan_detalle_id)
