"""Servicios de aplicación para hcm_planilla_detalle."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.hcm import (
    list_planilla_detalles as _list,
    get_planilla_detalle_by_id as _get,
    create_planilla_detalle as _create,
    update_planilla_detalle as _update,
    get_planilla_empleado_by_id as _get_planilla_empleado,
)
from app.modules.hcm.application.services.planilla_service import ensure_planilla_borrador
from app.modules.hcm.presentation.schemas import PlanillaDetalleCreate, PlanillaDetalleUpdate, PlanillaDetalleRead
from app.core.exceptions import NotFoundError


async def list_planilla_detalles(
    client_id: UUID,
    planilla_empleado_id: Optional[UUID] = None,
    tipo_concepto: Optional[str] = None,
) -> List[PlanillaDetalleRead]:
    rows = await _list(
        client_id=client_id,
        planilla_empleado_id=planilla_empleado_id,
        tipo_concepto=tipo_concepto,
    )
    return [PlanillaDetalleRead(**r) for r in rows]


async def get_planilla_detalle_by_id(
    client_id: UUID, planilla_detalle_id: UUID
) -> PlanillaDetalleRead:
    row = await _get(client_id, planilla_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle de planilla {planilla_detalle_id} no encontrado")
    return PlanillaDetalleRead(**row)


async def create_planilla_detalle(
    client_id: UUID, data: PlanillaDetalleCreate
) -> PlanillaDetalleRead:
    pe = await _get_planilla_empleado(client_id, data.planilla_empleado_id)
    if not pe:
        raise NotFoundError(
            f"Planilla empleado {data.planilla_empleado_id} no encontrado"
        )
    await ensure_planilla_borrador(client_id, pe["planilla_id"])
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return PlanillaDetalleRead(**row)


async def update_planilla_detalle(
    client_id: UUID, planilla_detalle_id: UUID, data: PlanillaDetalleUpdate
) -> PlanillaDetalleRead:
    det = await _get(client_id, planilla_detalle_id)
    if not det:
        raise NotFoundError(f"Detalle de planilla {planilla_detalle_id} no encontrado")
    pe = await _get_planilla_empleado(client_id, det["planilla_empleado_id"])
    if not pe:
        raise NotFoundError(
            f"Planilla empleado {det['planilla_empleado_id']} no encontrado"
        )
    await ensure_planilla_borrador(client_id, pe["planilla_id"])
    row = await _update(client_id, planilla_detalle_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Detalle de planilla {planilla_detalle_id} no encontrado")
    return PlanillaDetalleRead(**row)
