"""
Queries SQLAlchemy Core para hcm_planilla.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import HcmPlanillaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in HcmPlanillaTable.c}


async def list_planillas(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_planilla: Optional[str] = None,
    estado: Optional[str] = None,
    año: Optional[int] = None,
    mes: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Lista planillas del tenant."""
    query = select(HcmPlanillaTable).where(
        HcmPlanillaTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(HcmPlanillaTable.c.empresa_id == empresa_id)
    if tipo_planilla:
        query = query.where(HcmPlanillaTable.c.tipo_planilla == tipo_planilla)
    if estado:
        query = query.where(HcmPlanillaTable.c.estado == estado)
    if año is not None:
        query = query.where(HcmPlanillaTable.c["año"] == año)
    if mes is not None:
        query = query.where(HcmPlanillaTable.c.mes == mes)
    query = query.order_by(
        HcmPlanillaTable.c["año"].desc(),
        HcmPlanillaTable.c.mes.desc(),
    )
    return await execute_query(query, client_id=client_id)


async def get_planilla_by_id(client_id: UUID, planilla_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una planilla por id."""
    query = select(HcmPlanillaTable).where(
        and_(
            HcmPlanillaTable.c.cliente_id == client_id,
            HcmPlanillaTable.c.planilla_id == planilla_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_planilla(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una planilla."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("planilla_id", uuid4())
    stmt = insert(HcmPlanillaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_planilla_by_id(client_id, payload["planilla_id"])


async def update_planilla(
    client_id: UUID, planilla_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una planilla."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("planilla_id", "cliente_id")
    }
    if not payload:
        return await get_planilla_by_id(client_id, planilla_id)
    stmt = (
        update(HcmPlanillaTable)
        .where(
            and_(
                HcmPlanillaTable.c.cliente_id == client_id,
                HcmPlanillaTable.c.planilla_id == planilla_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_planilla_by_id(client_id, planilla_id)
