"""Queries para mps_plan_produccion_detalle. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_
from app.infrastructure.database.tables_erp import MpsPlanProduccionTable, MpsPlanProduccionDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in MpsPlanProduccionDetalleTable.c}


async def list_plan_produccion_detalle(
    client_id: UUID,
    plan_produccion_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    q = select(MpsPlanProduccionDetalleTable).where(MpsPlanProduccionDetalleTable.c.cliente_id == client_id)
    if plan_produccion_id:
        q = q.where(MpsPlanProduccionDetalleTable.c.plan_produccion_id == plan_produccion_id)
    if producto_id:
        q = q.where(MpsPlanProduccionDetalleTable.c.producto_id == producto_id)
    q = q.order_by(MpsPlanProduccionDetalleTable.c.fecha_inicio, MpsPlanProduccionDetalleTable.c.producto_id)
    return await execute_query(q, client_id=client_id)


async def get_plan_produccion_detalle_by_id(client_id: UUID, plan_detalle_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(MpsPlanProduccionDetalleTable).where(
        and_(
            MpsPlanProduccionDetalleTable.c.cliente_id == client_id,
            MpsPlanProduccionDetalleTable.c.plan_detalle_id == plan_detalle_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_plan_produccion_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("plan_detalle_id", uuid4())
    # ✅ Endurecimiento tenant:
    # - empresa_id es obligatorio en la tabla (NO NULL)
    # - la derivación debe ocurrir en la capa de servicio (para poder lanzar errores de negocio claros)
    if not payload.get("empresa_id"):
        raise ValueError("empresa_id es obligatorio para crear detalle de plan de producción")

    # Validar pertenencia y coherencia: el plan debe existir en el mismo tenant y su empresa_id debe coincidir
    plan_produccion_id = payload.get("plan_produccion_id")
    if not plan_produccion_id:
        raise ValueError("plan_produccion_id es obligatorio para crear detalle de plan de producción")

    q = select(MpsPlanProduccionTable.c.empresa_id).where(
        and_(
            MpsPlanProduccionTable.c.cliente_id == client_id,
            MpsPlanProduccionTable.c.plan_produccion_id == plan_produccion_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    if not rows:
        raise ValueError("plan_produccion_id no existe o no pertenece al tenant")
    if rows[0]["empresa_id"] != payload["empresa_id"]:
        raise ValueError("empresa_id no coincide con la empresa del plan de producción")
    await execute_insert(insert(MpsPlanProduccionDetalleTable).values(**payload), client_id=client_id)
    return await get_plan_produccion_detalle_by_id(client_id, payload["plan_detalle_id"])


async def update_plan_produccion_detalle(
    client_id: UUID, plan_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in ("plan_detalle_id", "cliente_id")}
    if not payload:
        return await get_plan_produccion_detalle_by_id(client_id, plan_detalle_id)
    stmt = update(MpsPlanProduccionDetalleTable).where(
        and_(
            MpsPlanProduccionDetalleTable.c.cliente_id == client_id,
            MpsPlanProduccionDetalleTable.c.plan_detalle_id == plan_detalle_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_plan_produccion_detalle_by_id(client_id, plan_detalle_id)
