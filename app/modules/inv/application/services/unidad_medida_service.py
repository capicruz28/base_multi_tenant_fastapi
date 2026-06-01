# app/modules/inv/application/services/unidad_medida_service.py
"""
Servicio de Unidad de Medida (INV). client_id siempre desde contexto, nunca desde body.
Aislamiento multi-empresa: empresa_id desde sesión JWT (company_scope).
"""
from typing import List
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.core.tenant.company_scope import (
    require_session_empresa_id,
    enforce_body_empresa_matches_session,
    ensure_empresa_in_tenant,
)
from app.infrastructure.database.queries.inv import (
    list_unidades_medida,
    get_unidad_medida_by_id,
    create_unidad_medida,
    update_unidad_medida,
)
from app.modules.inv.presentation.schemas import (
    UnidadMedidaCreate,
    UnidadMedidaUpdate,
    UnidadMedidaRead,
)


def _row_to_read(row: dict) -> UnidadMedidaRead:
    return UnidadMedidaRead(**row)


async def list_unidades_medida_servicio(
    client_id: UUID,
    solo_activos: bool = True,
) -> List[UnidadMedidaRead]:
    empresa_id = require_session_empresa_id()
    rows = await list_unidades_medida(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )
    return [_row_to_read(r) for r in rows]


async def get_unidad_medida_servicio(
    client_id: UUID,
    unidad_medida_id: UUID,
) -> UnidadMedidaRead:
    empresa_id = require_session_empresa_id()
    row = await get_unidad_medida_by_id(
        client_id=client_id,
        unidad_medida_id=unidad_medida_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Unidad de medida no encontrada")
    return _row_to_read(row)


async def create_unidad_medida_servicio(
    client_id: UUID,
    data: UnidadMedidaCreate,
) -> UnidadMedidaRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    payload = data.model_dump()
    payload["empresa_id"] = empresa_id
    row = await create_unidad_medida(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_unidad_medida_servicio(
    client_id: UUID,
    unidad_medida_id: UUID,
    data: UnidadMedidaUpdate,
) -> UnidadMedidaRead:
    empresa_id = require_session_empresa_id()
    row = await get_unidad_medida_by_id(
        client_id=client_id,
        unidad_medida_id=unidad_medida_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Unidad de medida no encontrada")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_unidad_medida(
        client_id=client_id,
        unidad_medida_id=unidad_medida_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)
