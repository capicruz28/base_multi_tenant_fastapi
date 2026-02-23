"""
Queries SQLAlchemy Core para hcm_planilla_empleado.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import HcmPlanillaEmpleadoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in HcmPlanillaEmpleadoTable.c}


async def list_planilla_empleados(
    client_id: UUID,
    planilla_id: Optional[UUID] = None,
    empleado_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Lista planilla-empleados del tenant."""
    query = select(HcmPlanillaEmpleadoTable).where(
        HcmPlanillaEmpleadoTable.c.cliente_id == client_id
    )
    if planilla_id:
        query = query.where(HcmPlanillaEmpleadoTable.c.planilla_id == planilla_id)
    if empleado_id:
        query = query.where(HcmPlanillaEmpleadoTable.c.empleado_id == empleado_id)
    query = query.order_by(HcmPlanillaEmpleadoTable.c.empleado_id)
    return await execute_query(query, client_id=client_id)


async def get_planilla_empleado_by_id(
    client_id: UUID, planilla_empleado_id: UUID
) -> Optional[Dict[str, Any]]:
    """Obtiene un planilla-empleado por id."""
    query = select(HcmPlanillaEmpleadoTable).where(
        and_(
            HcmPlanillaEmpleadoTable.c.cliente_id == client_id,
            HcmPlanillaEmpleadoTable.c.planilla_empleado_id == planilla_empleado_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_planilla_empleado(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un planilla-empleado."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("planilla_empleado_id", uuid4())
    stmt = insert(HcmPlanillaEmpleadoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_planilla_empleado_by_id(client_id, payload["planilla_empleado_id"])


async def update_planilla_empleado(
    client_id: UUID, planilla_empleado_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un planilla-empleado."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("planilla_empleado_id", "cliente_id")
    }
    if not payload:
        return await get_planilla_empleado_by_id(client_id, planilla_empleado_id)
    stmt = (
        update(HcmPlanillaEmpleadoTable)
        .where(
            and_(
                HcmPlanillaEmpleadoTable.c.cliente_id == client_id,
                HcmPlanillaEmpleadoTable.c.planilla_empleado_id == planilla_empleado_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_planilla_empleado_by_id(client_id, planilla_empleado_id)
