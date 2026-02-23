"""
Queries SQLAlchemy Core para log_despacho y log_despacho_guia.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import LogDespachoTable, LogDespachoGuiaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS_DESPACHO = {c.name for c in LogDespachoTable.c}
_COLUMNS_DESPACHO_GUIA = {c.name for c in LogDespachoGuiaTable.c}


async def list_despachos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    ruta_id: Optional[UUID] = None,
    vehiculo_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista despachos del tenant. Siempre filtra por cliente_id."""
    query = select(LogDespachoTable).where(
        LogDespachoTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(LogDespachoTable.c.empresa_id == empresa_id)
    if estado:
        query = query.where(LogDespachoTable.c.estado == estado)
    if ruta_id:
        query = query.where(LogDespachoTable.c.ruta_id == ruta_id)
    if vehiculo_id:
        query = query.where(LogDespachoTable.c.vehiculo_id == vehiculo_id)
    if fecha_desde:
        query = query.where(LogDespachoTable.c.fecha_programada >= fecha_desde)
    if fecha_hasta:
        query = query.where(LogDespachoTable.c.fecha_programada <= fecha_hasta)
    if buscar:
        search_filter = or_(
            LogDespachoTable.c.numero_despacho.ilike(f"%{buscar}%"),
            LogDespachoTable.c.conductor_nombre.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(LogDespachoTable.c.fecha_programada.desc())
    return await execute_query(query, client_id=client_id)


async def get_despacho_by_id(client_id: UUID, despacho_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un despacho por id. Exige cliente_id para no cruzar tenants."""
    query = select(LogDespachoTable).where(
        and_(
            LogDespachoTable.c.cliente_id == client_id,
            LogDespachoTable.c.despacho_id == despacho_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_despacho(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un despacho. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS_DESPACHO}
    payload["cliente_id"] = client_id
    payload.setdefault("despacho_id", uuid4())
    stmt = insert(LogDespachoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_despacho_by_id(client_id, payload["despacho_id"])


async def update_despacho(
    client_id: UUID, despacho_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un despacho. WHERE incluye cliente_id y despacho_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS_DESPACHO and k not in ("despacho_id", "cliente_id")
    }
    if not payload:
        return await get_despacho_by_id(client_id, despacho_id)
    stmt = (
        update(LogDespachoTable)
        .where(
            and_(
                LogDespachoTable.c.cliente_id == client_id,
                LogDespachoTable.c.despacho_id == despacho_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_despacho_by_id(client_id, despacho_id)


# ============================================================================
# DESPACHO-GUÍA
# ============================================================================

async def list_despacho_guias(
    client_id: UUID,
    despacho_id: Optional[UUID] = None,
    guia_remision_id: Optional[UUID] = None,
    estado_entrega: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista relaciones despacho-guía del tenant."""
    query = select(LogDespachoGuiaTable).where(
        LogDespachoGuiaTable.c.cliente_id == client_id
    )
    if despacho_id:
        query = query.where(LogDespachoGuiaTable.c.despacho_id == despacho_id)
    if guia_remision_id:
        query = query.where(LogDespachoGuiaTable.c.guia_remision_id == guia_remision_id)
    if estado_entrega:
        query = query.where(LogDespachoGuiaTable.c.estado_entrega == estado_entrega)
    query = query.order_by(LogDespachoGuiaTable.c.orden_entrega)
    return await execute_query(query, client_id=client_id)


async def get_despacho_guia_by_id(client_id: UUID, despacho_guia_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una relación despacho-guía por id."""
    query = select(LogDespachoGuiaTable).where(
        and_(
            LogDespachoGuiaTable.c.cliente_id == client_id,
            LogDespachoGuiaTable.c.despacho_guia_id == despacho_guia_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_despacho_guia(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una relación despacho-guía."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS_DESPACHO_GUIA}
    payload["cliente_id"] = client_id
    payload.setdefault("despacho_guia_id", uuid4())
    stmt = insert(LogDespachoGuiaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_despacho_guia_by_id(client_id, payload["despacho_guia_id"])


async def update_despacho_guia(
    client_id: UUID, despacho_guia_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una relación despacho-guía."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS_DESPACHO_GUIA and k not in ("despacho_guia_id", "cliente_id")
    }
    if not payload:
        return await get_despacho_guia_by_id(client_id, despacho_guia_id)
    stmt = (
        update(LogDespachoGuiaTable)
        .where(
            and_(
                LogDespachoGuiaTable.c.cliente_id == client_id,
                LogDespachoGuiaTable.c.despacho_guia_id == despacho_guia_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_despacho_guia_by_id(client_id, despacho_guia_id)
