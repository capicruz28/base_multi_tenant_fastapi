"""Servicio aplicación mnt_plan_mantenimiento."""
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.infrastructure.database.queries.mnt import (
    list_plan_mantenimiento as _list,
    get_plan_mantenimiento_by_id as _get,
    create_plan_mantenimiento as _create,
    update_plan_mantenimiento as _update,
)
from app.modules.mnt.presentation.schemas import (
    PlanMantenimientoCreate,
    PlanMantenimientoUpdate,
    PlanMantenimientoRead,
)
from app.core.exceptions import NotFoundError


async def list_plan_mantenimiento(
    client_id: UUID,
    activo_id: Optional[UUID] = None,
    tipo_mantenimiento: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
    empresa_id: Optional[UUID] = None,
    vence_desde: Optional[date] = None,
    vence_hasta: Optional[date] = None,
) -> List[PlanMantenimientoRead]:
    rows = await _list(
        client_id=client_id,
        activo_id=activo_id,
        tipo_mantenimiento=tipo_mantenimiento,
        es_activo=es_activo,
        buscar=buscar,
        empresa_id=empresa_id,
        vence_desde=vence_desde,
        vence_hasta=vence_hasta,
    )
    return [PlanMantenimientoRead(**r) for r in rows]


async def get_plan_mantenimiento_by_id(
    client_id: UUID, plan_mantenimiento_id: UUID
) -> PlanMantenimientoRead:
    row = await _get(client_id, plan_mantenimiento_id)
    if not row:
        raise NotFoundError(f"Plan mantenimiento {plan_mantenimiento_id} no encontrado")
    return PlanMantenimientoRead(**row)


async def create_plan_mantenimiento(
    client_id: UUID, data: PlanMantenimientoCreate
) -> PlanMantenimientoRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return PlanMantenimientoRead(**row)


async def update_plan_mantenimiento(
    client_id: UUID, plan_mantenimiento_id: UUID, data: PlanMantenimientoUpdate
) -> PlanMantenimientoRead:
    row = await _update(client_id, plan_mantenimiento_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Plan mantenimiento {plan_mantenimiento_id} no encontrado")
    return PlanMantenimientoRead(**row)


async def _set_plan_es_activo(
    client_id: UUID, plan_mantenimiento_id: UUID, nuevo_estado: bool
) -> PlanMantenimientoRead:
    """Baja/alta lógica del plan de mantenimiento (idempotente)."""
    current = await _get(client_id, plan_mantenimiento_id)
    if not current:
        raise NotFoundError(f"Plan mantenimiento {plan_mantenimiento_id} no encontrado")
    if bool(current.get("es_activo")) == nuevo_estado:
        return PlanMantenimientoRead(**current)
    row = await _update(client_id, plan_mantenimiento_id, {"es_activo": nuevo_estado})
    if not row:
        raise NotFoundError(f"Plan mantenimiento {plan_mantenimiento_id} no encontrado")
    return PlanMantenimientoRead(**row)


async def activar_plan_mantenimiento(
    client_id: UUID, plan_mantenimiento_id: UUID
) -> PlanMantenimientoRead:
    """Activa el plan (es_activo=1). Idempotente."""
    return await _set_plan_es_activo(client_id, plan_mantenimiento_id, True)


async def desactivar_plan_mantenimiento(
    client_id: UUID, plan_mantenimiento_id: UUID
) -> PlanMantenimientoRead:
    """Desactiva el plan (es_activo=0, baja lógica). Idempotente."""
    return await _set_plan_es_activo(client_id, plan_mantenimiento_id, False)
