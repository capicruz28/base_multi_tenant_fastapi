"""
Queries SQLAlchemy Core para pos_turno_caja.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PosTurnoCajaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PosTurnoCajaTable.c}


async def list_turnos_caja(
    client_id: UUID,
    punto_venta_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    cajero_usuario_id: Optional[UUID] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Lista turnos de caja del tenant."""
    query = select(PosTurnoCajaTable).where(
        PosTurnoCajaTable.c.cliente_id == client_id
    )
    if punto_venta_id:
        query = query.where(PosTurnoCajaTable.c.punto_venta_id == punto_venta_id)
    if estado:
        query = query.where(PosTurnoCajaTable.c.estado == estado)
    if cajero_usuario_id:
        query = query.where(PosTurnoCajaTable.c.cajero_usuario_id == cajero_usuario_id)
    if fecha_desde:
        query = query.where(PosTurnoCajaTable.c.fecha_apertura >= fecha_desde)
    if fecha_hasta:
        query = query.where(PosTurnoCajaTable.c.fecha_apertura <= fecha_hasta)
    query = query.order_by(PosTurnoCajaTable.c.fecha_apertura.desc())
    return await execute_query(query, client_id=client_id)


async def get_turno_caja_by_id(client_id: UUID, turno_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un turno de caja por id."""
    query = select(PosTurnoCajaTable).where(
        and_(
            PosTurnoCajaTable.c.cliente_id == client_id,
            PosTurnoCajaTable.c.turno_id == turno_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_turno_caja(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un turno de caja."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("turno_id", uuid4())
    stmt = insert(PosTurnoCajaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_turno_caja_by_id(client_id, payload["turno_id"])


async def update_turno_caja(
    client_id: UUID, turno_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un turno de caja (ej. cierre)."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("turno_id", "cliente_id")
    }
    if not payload:
        return await get_turno_caja_by_id(client_id, turno_id)
    stmt = (
        update(PosTurnoCajaTable)
        .where(
            and_(
                PosTurnoCajaTable.c.cliente_id == client_id,
                PosTurnoCajaTable.c.turno_id == turno_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_turno_caja_by_id(client_id, turno_id)
