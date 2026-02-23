"""
Queries SQLAlchemy Core para hcm_contrato.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import HcmContratoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in HcmContratoTable.c}


async def list_contratos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    empleado_id: Optional[UUID] = None,
    estado_contrato: Optional[str] = None,
    es_contrato_vigente: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """Lista contratos del tenant."""
    query = select(HcmContratoTable).where(
        HcmContratoTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(HcmContratoTable.c.empresa_id == empresa_id)
    if empleado_id:
        query = query.where(HcmContratoTable.c.empleado_id == empleado_id)
    if estado_contrato:
        query = query.where(HcmContratoTable.c.estado_contrato == estado_contrato)
    if es_contrato_vigente is not None:
        query = query.where(HcmContratoTable.c.es_contrato_vigente == es_contrato_vigente)
    query = query.order_by(HcmContratoTable.c.fecha_inicio.desc())
    return await execute_query(query, client_id=client_id)


async def get_contrato_by_id(client_id: UUID, contrato_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un contrato por id."""
    query = select(HcmContratoTable).where(
        and_(
            HcmContratoTable.c.cliente_id == client_id,
            HcmContratoTable.c.contrato_id == contrato_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_contrato(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un contrato."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("contrato_id", uuid4())
    stmt = insert(HcmContratoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_contrato_by_id(client_id, payload["contrato_id"])


async def update_contrato(
    client_id: UUID, contrato_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un contrato."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("contrato_id", "cliente_id")
    }
    if not payload:
        return await get_contrato_by_id(client_id, contrato_id)
    stmt = (
        update(HcmContratoTable)
        .where(
            and_(
                HcmContratoTable.c.cliente_id == client_id,
                HcmContratoTable.c.contrato_id == contrato_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_contrato_by_id(client_id, contrato_id)
