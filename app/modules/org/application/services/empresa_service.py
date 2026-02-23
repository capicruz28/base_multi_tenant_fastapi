# app/modules/org/application/services/empresa_service.py
"""
Servicio de Empresa (ORG). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.org import (
    list_empresas,
    get_empresa_by_id,
    create_empresa,
    update_empresa,
)
from app.modules.org.presentation.schemas import (
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaRead,
)


def _row_to_read(row: dict) -> EmpresaRead:
    return EmpresaRead(**row)


async def list_empresas_servicio(
    client_id: UUID,
    solo_activos: bool = True,
) -> List[EmpresaRead]:
    rows = await list_empresas(client_id=client_id, solo_activos=solo_activos)
    return [_row_to_read(r) for r in rows]


async def get_empresa_servicio(
    client_id: UUID,
    empresa_id: UUID,
) -> EmpresaRead:
    row = await get_empresa_by_id(client_id=client_id, empresa_id=empresa_id)
    if not row:
        raise NotFoundError(detail="Empresa no encontrada")
    return _row_to_read(row)


async def create_empresa_servicio(
    client_id: UUID,
    data: EmpresaCreate,
) -> EmpresaRead:
    payload = data.model_dump()
    row = await create_empresa(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_empresa_servicio(
    client_id: UUID,
    empresa_id: UUID,
    data: EmpresaUpdate,
) -> EmpresaRead:
    row = await get_empresa_by_id(client_id=client_id, empresa_id=empresa_id)
    if not row:
        raise NotFoundError(detail="Empresa no encontrada")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_empresa(client_id=client_id, empresa_id=empresa_id, data=payload)
    return _row_to_read(updated)
