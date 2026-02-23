"""
Queries SQLAlchemy Core para fin_asiento_contable y fin_asiento_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import FinAsientoContableTable, FinAsientoDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS_ASIENTO = {c.name for c in FinAsientoContableTable.c}
_COLUMNS_DETALLE = {c.name for c in FinAsientoDetalleTable.c}


async def list_asientos_contables(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    periodo_id: Optional[UUID] = None,
    tipo_asiento: Optional[str] = None,
    estado: Optional[str] = None,
    modulo_origen: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista asientos contables del tenant. Siempre filtra por cliente_id."""
    query = select(FinAsientoContableTable).where(
        FinAsientoContableTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(FinAsientoContableTable.c.empresa_id == empresa_id)
    if periodo_id:
        query = query.where(FinAsientoContableTable.c.periodo_id == periodo_id)
    if tipo_asiento:
        query = query.where(FinAsientoContableTable.c.tipo_asiento == tipo_asiento)
    if estado:
        query = query.where(FinAsientoContableTable.c.estado == estado)
    if modulo_origen:
        query = query.where(FinAsientoContableTable.c.modulo_origen == modulo_origen)
    if fecha_desde:
        query = query.where(FinAsientoContableTable.c.fecha_asiento >= fecha_desde)
    if fecha_hasta:
        query = query.where(FinAsientoContableTable.c.fecha_asiento <= fecha_hasta)
    if buscar:
        search_filter = or_(
            FinAsientoContableTable.c.numero_asiento.ilike(f"%{buscar}%"),
            FinAsientoContableTable.c.glosa.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(FinAsientoContableTable.c.fecha_asiento.desc(), FinAsientoContableTable.c.numero_asiento)
    return await execute_query(query, client_id=client_id)


async def get_asiento_contable_by_id(client_id: UUID, asiento_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un asiento contable por id. Exige cliente_id para no cruzar tenants."""
    query = select(FinAsientoContableTable).where(
        and_(
            FinAsientoContableTable.c.cliente_id == client_id,
            FinAsientoContableTable.c.asiento_id == asiento_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_asiento_contable(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un asiento contable. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS_ASIENTO}
    payload["cliente_id"] = client_id
    payload.setdefault("asiento_id", uuid4())
    stmt = insert(FinAsientoContableTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_asiento_contable_by_id(client_id, payload["asiento_id"])


async def update_asiento_contable(
    client_id: UUID, asiento_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un asiento contable. WHERE incluye cliente_id y asiento_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS_ASIENTO and k not in ("asiento_id", "cliente_id")
    }
    if not payload:
        return await get_asiento_contable_by_id(client_id, asiento_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(FinAsientoContableTable)
        .where(
            and_(
                FinAsientoContableTable.c.cliente_id == client_id,
                FinAsientoContableTable.c.asiento_id == asiento_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_asiento_contable_by_id(client_id, asiento_id)


# ============================================================================
# DETALLES DE ASIENTO CONTABLE
# ============================================================================

async def list_asiento_detalles(
    client_id: UUID,
    asiento_id: Optional[UUID] = None,
    cuenta_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """Lista detalles de asiento contable del tenant."""
    query = select(FinAsientoDetalleTable).where(
        FinAsientoDetalleTable.c.cliente_id == client_id
    )
    if asiento_id:
        query = query.where(FinAsientoDetalleTable.c.asiento_id == asiento_id)
    if cuenta_id:
        query = query.where(FinAsientoDetalleTable.c.cuenta_id == cuenta_id)
    query = query.order_by(FinAsientoDetalleTable.c.item)
    return await execute_query(query, client_id=client_id)


async def get_asiento_detalle_by_id(client_id: UUID, asiento_detalle_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un detalle por id."""
    query = select(FinAsientoDetalleTable).where(
        and_(
            FinAsientoDetalleTable.c.cliente_id == client_id,
            FinAsientoDetalleTable.c.asiento_detalle_id == asiento_detalle_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_asiento_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un detalle de asiento contable."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS_DETALLE}
    payload["cliente_id"] = client_id
    payload.setdefault("asiento_detalle_id", uuid4())
    stmt = insert(FinAsientoDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_asiento_detalle_by_id(client_id, payload["asiento_detalle_id"])


async def update_asiento_detalle(
    client_id: UUID, asiento_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un detalle de asiento contable."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS_DETALLE and k not in ("asiento_detalle_id", "cliente_id")
    }
    if not payload:
        return await get_asiento_detalle_by_id(client_id, asiento_detalle_id)
    stmt = (
        update(FinAsientoDetalleTable)
        .where(
            and_(
                FinAsientoDetalleTable.c.cliente_id == client_id,
                FinAsientoDetalleTable.c.asiento_detalle_id == asiento_detalle_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_asiento_detalle_by_id(client_id, asiento_detalle_id)
