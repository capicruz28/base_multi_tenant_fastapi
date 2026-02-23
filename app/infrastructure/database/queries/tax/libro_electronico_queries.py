"""Queries para tax_libro_electronico. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_
from app.infrastructure.database.tables_erp import TaxLibroElectronicoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in TaxLibroElectronicoTable.c}


async def list_libro_electronico(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_libro: Optional[str] = None,
    anio: Optional[int] = None,
    mes: Optional[int] = None,
    estado: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(TaxLibroElectronicoTable).where(TaxLibroElectronicoTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(TaxLibroElectronicoTable.c.empresa_id == empresa_id)
    if tipo_libro:
        q = q.where(TaxLibroElectronicoTable.c.tipo_libro == tipo_libro)
    if anio is not None:
        q = q.where(TaxLibroElectronicoTable.c["año"] == anio)
    if mes is not None:
        q = q.where(TaxLibroElectronicoTable.c.mes == mes)
    if estado:
        q = q.where(TaxLibroElectronicoTable.c.estado == estado)
    q = q.order_by(TaxLibroElectronicoTable.c["año"].desc(), TaxLibroElectronicoTable.c.mes.desc(), TaxLibroElectronicoTable.c.tipo_libro)
    return await execute_query(q, client_id=client_id)


async def get_libro_electronico_by_id(client_id: UUID, libro_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(TaxLibroElectronicoTable).where(
        and_(
            TaxLibroElectronicoTable.c.cliente_id == client_id,
            TaxLibroElectronicoTable.c.libro_id == libro_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_libro_electronico(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("libro_id", uuid4())
    await execute_insert(insert(TaxLibroElectronicoTable).values(**payload), client_id=client_id)
    return await get_libro_electronico_by_id(client_id, payload["libro_id"])


async def update_libro_electronico(
    client_id: UUID, libro_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("libro_id", "cliente_id")}
    if not payload:
        return await get_libro_electronico_by_id(client_id, libro_id)
    stmt = update(TaxLibroElectronicoTable).where(
        and_(
            TaxLibroElectronicoTable.c.cliente_id == client_id,
            TaxLibroElectronicoTable.c.libro_id == libro_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_libro_electronico_by_id(client_id, libro_id)
