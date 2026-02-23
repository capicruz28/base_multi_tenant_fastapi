"""
Queries SQLAlchemy Core para hcm_vacaciones.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import HcmVacacionesTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in HcmVacacionesTable.c}


async def list_vacaciones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    empleado_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    año_periodo: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Lista vacaciones del tenant."""
    query = select(HcmVacacionesTable).where(
        HcmVacacionesTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(HcmVacacionesTable.c.empresa_id == empresa_id)
    if empleado_id:
        query = query.where(HcmVacacionesTable.c.empleado_id == empleado_id)
    if estado:
        query = query.where(HcmVacacionesTable.c.estado == estado)
    if año_periodo is not None:
        query = query.where(HcmVacacionesTable.c.año_periodo == año_periodo)
    query = query.order_by(HcmVacacionesTable.c.año_periodo.desc())
    return await execute_query(query, client_id=client_id)


async def get_vacaciones_by_id(client_id: UUID, vacaciones_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un registro de vacaciones por id."""
    query = select(HcmVacacionesTable).where(
        and_(
            HcmVacacionesTable.c.cliente_id == client_id,
            HcmVacacionesTable.c.vacaciones_id == vacaciones_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_vacaciones(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un registro de vacaciones."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("vacaciones_id", uuid4())
    stmt = insert(HcmVacacionesTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_vacaciones_by_id(client_id, payload["vacaciones_id"])


async def update_vacaciones(
    client_id: UUID, vacaciones_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un registro de vacaciones."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("vacaciones_id", "cliente_id")
    }
    if not payload:
        return await get_vacaciones_by_id(client_id, vacaciones_id)
    stmt = (
        update(HcmVacacionesTable)
        .where(
            and_(
                HcmVacacionesTable.c.cliente_id == client_id,
                HcmVacacionesTable.c.vacaciones_id == vacaciones_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_vacaciones_by_id(client_id, vacaciones_id)
