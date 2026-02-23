"""Servicio aplicación mrp_necesidad_bruta."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mrp import (
    list_necesidad_bruta as _list,
    get_necesidad_bruta_by_id as _get,
    create_necesidad_bruta as _create,
    update_necesidad_bruta as _update,
)
from app.modules.mrp.presentation.schemas import NecesidadBrutaCreate, NecesidadBrutaUpdate, NecesidadBrutaRead
from app.core.exceptions import NotFoundError


async def list_necesidad_bruta(
    client_id: UUID,
    plan_maestro_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    origen: Optional[str] = None,
) -> List[NecesidadBrutaRead]:
    rows = await _list(client_id=client_id, plan_maestro_id=plan_maestro_id, producto_id=producto_id, origen=origen)
    return [NecesidadBrutaRead(**r) for r in rows]


async def get_necesidad_bruta_by_id(client_id: UUID, necesidad_id: UUID) -> NecesidadBrutaRead:
    row = await _get(client_id, necesidad_id)
    if not row:
        raise NotFoundError(f"Necesidad bruta {necesidad_id} no encontrada")
    return NecesidadBrutaRead(**row)


async def create_necesidad_bruta(client_id: UUID, data: NecesidadBrutaCreate) -> NecesidadBrutaRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return NecesidadBrutaRead(**row)


async def update_necesidad_bruta(client_id: UUID, necesidad_id: UUID, data: NecesidadBrutaUpdate) -> NecesidadBrutaRead:
    row = await _update(client_id, necesidad_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Necesidad bruta {necesidad_id} no encontrada")
    return NecesidadBrutaRead(**row)
