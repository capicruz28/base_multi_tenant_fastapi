"""
Servicios de aplicación para qms_parametro_calidad.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.qms import (
    list_parametros_calidad as _list_parametros_calidad,
    get_parametro_calidad_by_id as _get_parametro_calidad_by_id,
    create_parametro_calidad as _create_parametro_calidad,
    update_parametro_calidad as _update_parametro_calidad,
)
from app.modules.qms.presentation.schemas import (
    ParametroCalidadCreate,
    ParametroCalidadUpdate,
    ParametroCalidadRead,
)
from app.core.exceptions import NotFoundError


async def list_parametros_calidad(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_parametro: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[ParametroCalidadRead]:
    """Lista parámetros de calidad del tenant."""
    rows = await _list_parametros_calidad(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_parametro=tipo_parametro,
        solo_activos=solo_activos,
        buscar=buscar
    )
    return [ParametroCalidadRead(**row) for row in rows]


async def get_parametro_calidad_by_id(client_id: UUID, parametro_id: UUID) -> ParametroCalidadRead:
    """Obtiene un parámetro por id."""
    row = await _get_parametro_calidad_by_id(client_id, parametro_id)
    if not row:
        raise NotFoundError(f"Parámetro de calidad {parametro_id} no encontrado")
    return ParametroCalidadRead(**row)


async def create_parametro_calidad(client_id: UUID, data: ParametroCalidadCreate) -> ParametroCalidadRead:
    """Crea un parámetro de calidad."""
    row = await _create_parametro_calidad(client_id, data.model_dump(exclude_none=True))
    return ParametroCalidadRead(**row)


async def update_parametro_calidad(
    client_id: UUID, parametro_id: UUID, data: ParametroCalidadUpdate
) -> ParametroCalidadRead:
    """Actualiza un parámetro de calidad."""
    row = await _update_parametro_calidad(
        client_id, parametro_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Parámetro de calidad {parametro_id} no encontrado")
    return ParametroCalidadRead(**row)
