# app/modules/org/application/services/departamento_service.py
"""Servicio de Departamento (ORG). client_id desde contexto."""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.org import (
    list_departamentos,
    get_departamento_by_id,
    create_departamento,
    update_departamento,
)
from app.modules.org.presentation.schemas import (
    DepartamentoCreate,
    DepartamentoUpdate,
    DepartamentoRead,
)


def _row_to_read(row: dict) -> DepartamentoRead:
    return DepartamentoRead(**row)


async def list_departamentos_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
) -> List[DepartamentoRead]:
    rows = await list_departamentos(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )
    return [_row_to_read(r) for r in rows]


async def get_departamento_servicio(
    client_id: UUID,
    departamento_id: UUID,
) -> DepartamentoRead:
    row = await get_departamento_by_id(
        client_id=client_id,
        departamento_id=departamento_id,
    )
    if not row:
        raise NotFoundError(detail="Departamento no encontrado")
    return _row_to_read(row)


async def create_departamento_servicio(
    client_id: UUID,
    data: DepartamentoCreate,
) -> DepartamentoRead:
    payload = data.model_dump()
    row = await create_departamento(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_departamento_servicio(
    client_id: UUID,
    departamento_id: UUID,
    data: DepartamentoUpdate,
) -> DepartamentoRead:
    row = await get_departamento_by_id(
        client_id=client_id,
        departamento_id=departamento_id,
    )
    if not row:
        raise NotFoundError(detail="Departamento no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_departamento(
        client_id=client_id,
        departamento_id=departamento_id,
        data=payload,
    )
    return _row_to_read(updated)
