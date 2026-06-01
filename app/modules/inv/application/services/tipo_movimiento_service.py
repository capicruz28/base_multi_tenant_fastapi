# app/modules/inv/application/services/tipo_movimiento_service.py
"""
Servicio de Tipo de Movimiento (INV). client_id siempre desde contexto, nunca desde body.
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
    list_tipos_movimiento,
    get_tipo_movimiento_by_id,
    create_tipo_movimiento,
    update_tipo_movimiento,
)
from app.modules.inv.presentation.schemas import (
    TipoMovimientoCreate,
    TipoMovimientoUpdate,
    TipoMovimientoRead,
)


def _row_to_read(row: dict) -> TipoMovimientoRead:
    return TipoMovimientoRead(**row)


async def list_tipos_movimiento_servicio(
    client_id: UUID,
    solo_activos: bool = True,
) -> List[TipoMovimientoRead]:
    empresa_id = require_session_empresa_id()
    rows = await list_tipos_movimiento(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )
    return [_row_to_read(r) for r in rows]


async def get_tipo_movimiento_servicio(
    client_id: UUID,
    tipo_movimiento_id: UUID,
) -> TipoMovimientoRead:
    empresa_id = require_session_empresa_id()
    row = await get_tipo_movimiento_by_id(
        client_id=client_id,
        tipo_movimiento_id=tipo_movimiento_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Tipo de movimiento no encontrado")
    return _row_to_read(row)


async def create_tipo_movimiento_servicio(
    client_id: UUID,
    data: TipoMovimientoCreate,
) -> TipoMovimientoRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    payload = data.model_dump()
    payload["empresa_id"] = empresa_id
    row = await create_tipo_movimiento(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_tipo_movimiento_servicio(
    client_id: UUID,
    tipo_movimiento_id: UUID,
    data: TipoMovimientoUpdate,
) -> TipoMovimientoRead:
    empresa_id = require_session_empresa_id()
    row = await get_tipo_movimiento_by_id(
        client_id=client_id,
        tipo_movimiento_id=tipo_movimiento_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Tipo de movimiento no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_tipo_movimiento(
        client_id=client_id,
        tipo_movimiento_id=tipo_movimiento_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)
