"""
Queries SQLAlchemy Core para hcm_asistencia.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import HcmAsistenciaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in HcmAsistenciaTable.c}


async def list_asistencias(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    empleado_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    tipo_asistencia: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista asistencias del tenant."""
    query = select(HcmAsistenciaTable).where(
        HcmAsistenciaTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(HcmAsistenciaTable.c.empresa_id == empresa_id)
    if empleado_id:
        query = query.where(HcmAsistenciaTable.c.empleado_id == empleado_id)
    if fecha_desde:
        query = query.where(HcmAsistenciaTable.c.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.where(HcmAsistenciaTable.c.fecha <= fecha_hasta)
    if tipo_asistencia:
        query = query.where(HcmAsistenciaTable.c.tipo_asistencia == tipo_asistencia)
    query = query.order_by(HcmAsistenciaTable.c.fecha.desc())
    return await execute_query(query, client_id=client_id)


async def get_asistencia_by_id(client_id: UUID, asistencia_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una asistencia por id."""
    query = select(HcmAsistenciaTable).where(
        and_(
            HcmAsistenciaTable.c.cliente_id == client_id,
            HcmAsistenciaTable.c.asistencia_id == asistencia_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_asistencia(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una asistencia."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("asistencia_id", uuid4())
    stmt = insert(HcmAsistenciaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_asistencia_by_id(client_id, payload["asistencia_id"])


async def update_asistencia(
    client_id: UUID, asistencia_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una asistencia."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("asistencia_id", "cliente_id")
    }
    if not payload:
        return await get_asistencia_by_id(client_id, asistencia_id)
    stmt = (
        update(HcmAsistenciaTable)
        .where(
            and_(
                HcmAsistenciaTable.c.cliente_id == client_id,
                HcmAsistenciaTable.c.asistencia_id == asistencia_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_asistencia_by_id(client_id, asistencia_id)
