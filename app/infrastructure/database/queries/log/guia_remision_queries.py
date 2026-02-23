"""
Queries SQLAlchemy Core para log_guia_remision y log_guia_remision_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import LogGuiaRemisionTable, LogGuiaRemisionDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS_GUIA = {c.name for c in LogGuiaRemisionTable.c}
_COLUMNS_DETALLE = {c.name for c in LogGuiaRemisionDetalleTable.c}


async def list_guias_remision(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    motivo_traslado: Optional[str] = None,
    transportista_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista guías de remisión del tenant. Siempre filtra por cliente_id."""
    query = select(LogGuiaRemisionTable).where(
        LogGuiaRemisionTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(LogGuiaRemisionTable.c.empresa_id == empresa_id)
    if estado:
        query = query.where(LogGuiaRemisionTable.c.estado == estado)
    if motivo_traslado:
        query = query.where(LogGuiaRemisionTable.c.motivo_traslado == motivo_traslado)
    if transportista_id:
        query = query.where(LogGuiaRemisionTable.c.transportista_id == transportista_id)
    if fecha_desde:
        query = query.where(LogGuiaRemisionTable.c.fecha_emision >= fecha_desde)
    if fecha_hasta:
        query = query.where(LogGuiaRemisionTable.c.fecha_emision <= fecha_hasta)
    if buscar:
        search_filter = or_(
            LogGuiaRemisionTable.c.numero.ilike(f"%{buscar}%"),
            LogGuiaRemisionTable.c.destinatario_razon_social.ilike(f"%{buscar}%"),
            LogGuiaRemisionTable.c.vehiculo_placa.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(LogGuiaRemisionTable.c.fecha_emision.desc())
    return await execute_query(query, client_id=client_id)


async def get_guia_remision_by_id(client_id: UUID, guia_remision_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una guía de remisión por id. Exige cliente_id para no cruzar tenants."""
    query = select(LogGuiaRemisionTable).where(
        and_(
            LogGuiaRemisionTable.c.cliente_id == client_id,
            LogGuiaRemisionTable.c.guia_remision_id == guia_remision_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_guia_remision(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una guía de remisión. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS_GUIA}
    payload["cliente_id"] = client_id
    payload.setdefault("guia_remision_id", uuid4())
    stmt = insert(LogGuiaRemisionTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_guia_remision_by_id(client_id, payload["guia_remision_id"])


async def update_guia_remision(
    client_id: UUID, guia_remision_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una guía de remisión. WHERE incluye cliente_id y guia_remision_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS_GUIA and k not in ("guia_remision_id", "cliente_id")
    }
    if not payload:
        return await get_guia_remision_by_id(client_id, guia_remision_id)
    stmt = (
        update(LogGuiaRemisionTable)
        .where(
            and_(
                LogGuiaRemisionTable.c.cliente_id == client_id,
                LogGuiaRemisionTable.c.guia_remision_id == guia_remision_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_guia_remision_by_id(client_id, guia_remision_id)


# ============================================================================
# DETALLES DE GUÍA DE REMISIÓN
# ============================================================================

async def list_guia_remision_detalles(
    client_id: UUID,
    guia_remision_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """Lista detalles de guía de remisión del tenant."""
    query = select(LogGuiaRemisionDetalleTable).where(
        LogGuiaRemisionDetalleTable.c.cliente_id == client_id
    )
    if guia_remision_id:
        query = query.where(LogGuiaRemisionDetalleTable.c.guia_remision_id == guia_remision_id)
    if producto_id:
        query = query.where(LogGuiaRemisionDetalleTable.c.producto_id == producto_id)
    query = query.order_by(LogGuiaRemisionDetalleTable.c.producto_id)
    return await execute_query(query, client_id=client_id)


async def get_guia_remision_detalle_by_id(client_id: UUID, guia_detalle_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un detalle por id."""
    query = select(LogGuiaRemisionDetalleTable).where(
        and_(
            LogGuiaRemisionDetalleTable.c.cliente_id == client_id,
            LogGuiaRemisionDetalleTable.c.guia_detalle_id == guia_detalle_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_guia_remision_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un detalle de guía de remisión."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS_DETALLE}
    payload["cliente_id"] = client_id
    payload.setdefault("guia_detalle_id", uuid4())
    stmt = insert(LogGuiaRemisionDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_guia_remision_detalle_by_id(client_id, payload["guia_detalle_id"])


async def update_guia_remision_detalle(
    client_id: UUID, guia_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un detalle de guía de remisión."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS_DETALLE and k not in ("guia_detalle_id", "cliente_id")
    }
    if not payload:
        return await get_guia_remision_detalle_by_id(client_id, guia_detalle_id)
    stmt = (
        update(LogGuiaRemisionDetalleTable)
        .where(
            and_(
                LogGuiaRemisionDetalleTable.c.cliente_id == client_id,
                LogGuiaRemisionDetalleTable.c.guia_detalle_id == guia_detalle_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_guia_remision_detalle_by_id(client_id, guia_detalle_id)
