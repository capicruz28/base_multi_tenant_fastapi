"""Queries para mps_pronostico_demanda. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import MpsPronosticoDemandaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MpsPronosticoDemandaTable.c}


async def list_pronostico_demanda(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    anio: Optional[int] = None,
    mes: Optional[int] = None,
) -> List[Dict[str, Any]]:
    q = select(MpsPronosticoDemandaTable).where(MpsPronosticoDemandaTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(MpsPronosticoDemandaTable.c.empresa_id == empresa_id)
    if producto_id:
        q = q.where(MpsPronosticoDemandaTable.c.producto_id == producto_id)
    if anio is not None:
        q = q.where(MpsPronosticoDemandaTable.c["año"] == anio)
    if mes is not None:
        q = q.where(MpsPronosticoDemandaTable.c.mes == mes)
    q = q.order_by(MpsPronosticoDemandaTable.c["año"].desc(), MpsPronosticoDemandaTable.c.mes.desc(), MpsPronosticoDemandaTable.c.producto_id)
    return await execute_query(q, client_id=client_id)


async def get_pronostico_demanda_by_id(client_id: UUID, pronostico_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MpsPronosticoDemandaTable).where(
        and_(
            MpsPronosticoDemandaTable.c.cliente_id == client_id,
            MpsPronosticoDemandaTable.c.pronostico_id == pronostico_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_pronostico_demanda(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("pronostico_id", uuid4())
    await execute_insert(insert(MpsPronosticoDemandaTable).values(**payload), client_id=client_id)
    return await get_pronostico_demanda_by_id(client_id, payload["pronostico_id"])


async def update_pronostico_demanda(
    client_id: UUID, pronostico_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("pronostico_id", "cliente_id")}
    if not payload:
        return await get_pronostico_demanda_by_id(client_id, pronostico_id)
    stmt = update(MpsPronosticoDemandaTable).where(
        and_(
            MpsPronosticoDemandaTable.c.cliente_id == client_id,
            MpsPronosticoDemandaTable.c.pronostico_id == pronostico_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_pronostico_demanda_by_id(client_id, pronostico_id)
