# app/modules/org/application/services/parametro_service.py
"""Servicio de Parámetro Sistema (ORG). client_id desde contexto."""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.org import (
    list_parametros,
    get_parametro_by_id,
    create_parametro,
    update_parametro,
)
from app.modules.org.presentation.schemas import (
    ParametroCreate,
    ParametroUpdate,
    ParametroRead,
)


def _row_to_read(row: dict) -> ParametroRead:
    return ParametroRead(**row)


async def list_parametros_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    modulo_codigo: Optional[str] = None,
    solo_activos: bool = True,
) -> List[ParametroRead]:
    rows = await list_parametros(
        client_id=client_id,
        empresa_id=empresa_id,
        modulo_codigo=modulo_codigo,
        solo_activos=solo_activos,
    )
    return [_row_to_read(r) for r in rows]


async def get_parametro_servicio(
    client_id: UUID,
    parametro_id: UUID,
) -> ParametroRead:
    row = await get_parametro_by_id(
        client_id=client_id,
        parametro_id=parametro_id,
    )
    if not row:
        raise NotFoundError(detail="Parámetro no encontrado")
    return _row_to_read(row)


async def create_parametro_servicio(
    client_id: UUID,
    data: ParametroCreate,
) -> ParametroRead:
    payload = data.model_dump()
    row = await create_parametro(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_parametro_servicio(
    client_id: UUID,
    parametro_id: UUID,
    data: ParametroUpdate,
) -> ParametroRead:
    row = await get_parametro_by_id(
        client_id=client_id,
        parametro_id=parametro_id,
    )
    if not row:
        raise NotFoundError(detail="Parámetro no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_parametro(
        client_id=client_id,
        parametro_id=parametro_id,
        data=payload,
    )
    return _row_to_read(updated)
