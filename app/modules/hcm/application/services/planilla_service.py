"""Servicios de aplicación para hcm_planilla."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.hcm import (
    list_planillas as _list,
    get_planilla_by_id as _get,
    create_planilla as _create,
    update_planilla as _update,
)
from app.modules.hcm.presentation.schemas import PlanillaCreate, PlanillaUpdate, PlanillaRead
from app.core.exceptions import NotFoundError


async def list_planillas(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_planilla: Optional[str] = None,
    estado: Optional[str] = None,
    año: Optional[int] = None,
    mes: Optional[int] = None,
) -> List[PlanillaRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_planilla=tipo_planilla,
        estado=estado,
        año=año,
        mes=mes,
    )
    return [PlanillaRead(**r) for r in rows]


async def get_planilla_by_id(client_id: UUID, planilla_id: UUID) -> PlanillaRead:
    row = await _get(client_id, planilla_id)
    if not row:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    return PlanillaRead(**row)


async def create_planilla(client_id: UUID, data: PlanillaCreate) -> PlanillaRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return PlanillaRead(**row)


async def update_planilla(client_id: UUID, planilla_id: UUID, data: PlanillaUpdate) -> PlanillaRead:
    row = await _update(client_id, planilla_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    return PlanillaRead(**row)
