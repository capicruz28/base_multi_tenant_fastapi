"""
Queries SQLAlchemy Core para hcm_planilla_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import HcmPlanillaDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in HcmPlanillaDetalleTable.c}


async def list_planilla_detalles(
    client_id: UUID,
    planilla_empleado_id: Optional[UUID] = None,
    tipo_concepto: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista detalles de planilla del tenant."""
    query = select(HcmPlanillaDetalleTable).where(
        HcmPlanillaDetalleTable.c.cliente_id == client_id
    )
    if planilla_empleado_id:
        query = query.where(
            HcmPlanillaDetalleTable.c.planilla_empleado_id == planilla_empleado_id
        )
    if tipo_concepto:
        query = query.where(HcmPlanillaDetalleTable.c.tipo_concepto == tipo_concepto)
    query = query.order_by(HcmPlanillaDetalleTable.c.planilla_empleado_id, HcmPlanillaDetalleTable.c.tipo_concepto)
    return await execute_query(query, client_id=client_id)


async def get_planilla_detalle_by_id(
    client_id: UUID, planilla_detalle_id: UUID
) -> Optional[Dict[str, Any]]:
    """Obtiene un detalle de planilla por id."""
    query = select(HcmPlanillaDetalleTable).where(
        and_(
            HcmPlanillaDetalleTable.c.cliente_id == client_id,
            HcmPlanillaDetalleTable.c.planilla_detalle_id == planilla_detalle_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_planilla_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un detalle de planilla."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("planilla_detalle_id", uuid4())
    stmt = insert(HcmPlanillaDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_planilla_detalle_by_id(client_id, payload["planilla_detalle_id"])


async def update_planilla_detalle(
    client_id: UUID, planilla_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un detalle de planilla."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("planilla_detalle_id", "cliente_id")
    }
    if not payload:
        return await get_planilla_detalle_by_id(client_id, planilla_detalle_id)
    stmt = (
        update(HcmPlanillaDetalleTable)
        .where(
            and_(
                HcmPlanillaDetalleTable.c.cliente_id == client_id,
                HcmPlanillaDetalleTable.c.planilla_detalle_id == planilla_detalle_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_planilla_detalle_by_id(client_id, planilla_detalle_id)
