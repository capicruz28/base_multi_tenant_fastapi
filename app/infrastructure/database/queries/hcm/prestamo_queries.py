"""
Queries SQLAlchemy Core para hcm_prestamo.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import HcmPrestamoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in HcmPrestamoTable.c}


async def list_prestamos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    empleado_id: Optional[UUID] = None,
    estado: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista préstamos del tenant."""
    query = select(HcmPrestamoTable).where(
        HcmPrestamoTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(HcmPrestamoTable.c.empresa_id == empresa_id)
    if empleado_id:
        query = query.where(HcmPrestamoTable.c.empleado_id == empleado_id)
    if estado:
        query = query.where(HcmPrestamoTable.c.estado == estado)
    query = query.order_by(HcmPrestamoTable.c.fecha_prestamo.desc())
    return await execute_query(query, client_id=client_id)


async def get_prestamo_by_id(client_id: UUID, prestamo_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un préstamo por id."""
    query = select(HcmPrestamoTable).where(
        and_(
            HcmPrestamoTable.c.cliente_id == client_id,
            HcmPrestamoTable.c.prestamo_id == prestamo_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_prestamo(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un préstamo."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("prestamo_id", uuid4())
    stmt = insert(HcmPrestamoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_prestamo_by_id(client_id, payload["prestamo_id"])


async def update_prestamo(
    client_id: UUID, prestamo_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un préstamo."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("prestamo_id", "cliente_id")
    }
    if not payload:
        return await get_prestamo_by_id(client_id, prestamo_id)
    stmt = (
        update(HcmPrestamoTable)
        .where(
            and_(
                HcmPrestamoTable.c.cliente_id == client_id,
                HcmPrestamoTable.c.prestamo_id == prestamo_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_prestamo_by_id(client_id, prestamo_id)
