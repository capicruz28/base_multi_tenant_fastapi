"""
Servicios de aplicación para qms_plan_inspeccion y qms_plan_inspeccion_detalle.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.qms import (
    list_planes_inspeccion as _list_planes_inspeccion,
    get_plan_inspeccion_by_id as _get_plan_inspeccion_by_id,
    create_plan_inspeccion as _create_plan_inspeccion,
    update_plan_inspeccion as _update_plan_inspeccion,
    list_plan_inspeccion_detalles as _list_plan_inspeccion_detalles,
    get_plan_inspeccion_detalle_by_id as _get_plan_inspeccion_detalle_by_id,
    create_plan_inspeccion_detalle as _create_plan_inspeccion_detalle,
    update_plan_inspeccion_detalle as _update_plan_inspeccion_detalle,
)
from app.modules.qms.presentation.schemas import (
    PlanInspeccionCreate,
    PlanInspeccionUpdate,
    PlanInspeccionRead,
    PlanInspeccionDetalleCreate,
    PlanInspeccionDetalleUpdate,
    PlanInspeccionDetalleRead,
)
from app.core.exceptions import NotFoundError


async def list_planes_inspeccion(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    categoria_id: Optional[UUID] = None,
    tipo_inspeccion: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[PlanInspeccionRead]:
    """Lista planes de inspección del tenant."""
    rows = await _list_planes_inspeccion(
        client_id=client_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        categoria_id=categoria_id,
        tipo_inspeccion=tipo_inspeccion,
        solo_activos=solo_activos,
        buscar=buscar
    )
    return [PlanInspeccionRead(**row) for row in rows]


async def get_plan_inspeccion_by_id(client_id: UUID, plan_inspeccion_id: UUID) -> PlanInspeccionRead:
    """Obtiene un plan por id."""
    row = await _get_plan_inspeccion_by_id(client_id, plan_inspeccion_id)
    if not row:
        raise NotFoundError(f"Plan de inspección {plan_inspeccion_id} no encontrado")
    return PlanInspeccionRead(**row)


async def create_plan_inspeccion(client_id: UUID, data: PlanInspeccionCreate) -> PlanInspeccionRead:
    """Crea un plan de inspección."""
    row = await _create_plan_inspeccion(client_id, data.model_dump(exclude_none=True))
    return PlanInspeccionRead(**row)


async def update_plan_inspeccion(
    client_id: UUID, plan_inspeccion_id: UUID, data: PlanInspeccionUpdate
) -> PlanInspeccionRead:
    """Actualiza un plan de inspección."""
    row = await _update_plan_inspeccion(
        client_id, plan_inspeccion_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Plan de inspección {plan_inspeccion_id} no encontrado")
    return PlanInspeccionRead(**row)


async def list_plan_inspeccion_detalles(
    client_id: UUID, plan_inspeccion_id: UUID
) -> List[PlanInspeccionDetalleRead]:
    """Lista detalles de un plan de inspección."""
    rows = await _list_plan_inspeccion_detalles(client_id, plan_inspeccion_id)
    return [PlanInspeccionDetalleRead(**row) for row in rows]


async def get_plan_inspeccion_detalle_by_id(
    client_id: UUID, plan_detalle_id: UUID
) -> PlanInspeccionDetalleRead:
    """Obtiene un detalle por id."""
    row = await _get_plan_inspeccion_detalle_by_id(client_id, plan_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle de plan {plan_detalle_id} no encontrado")
    return PlanInspeccionDetalleRead(**row)


async def create_plan_inspeccion_detalle(
    client_id: UUID, data: PlanInspeccionDetalleCreate
) -> PlanInspeccionDetalleRead:
    """Crea un detalle de plan."""
    row = await _create_plan_inspeccion_detalle(client_id, data.model_dump(exclude_none=True))
    return PlanInspeccionDetalleRead(**row)


async def update_plan_inspeccion_detalle(
    client_id: UUID, plan_detalle_id: UUID, data: PlanInspeccionDetalleUpdate
) -> PlanInspeccionDetalleRead:
    """Actualiza un detalle de plan."""
    row = await _update_plan_inspeccion_detalle(
        client_id, plan_detalle_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Detalle de plan {plan_detalle_id} no encontrado")
    return PlanInspeccionDetalleRead(**row)
