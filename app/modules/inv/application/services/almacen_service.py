# app/modules/inv/application/services/almacen_service.py
"""
Servicio de Almacén (INV). client_id siempre desde contexto, nunca desde body.
Aislamiento multi-empresa: empresa_id desde sesión JWT (company_scope).
CREATE: UoW + InvCodigoGenerationService (sequence_key inv_almacen).
UPDATE: BR-IMM — código inmutable (omitido del schema; sin lógica de código).
"""
from typing import List, Optional, Union
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.core.tenant.company_scope import (
    require_session_empresa_id,
    enforce_body_empresa_matches_session,
    ensure_empresa_in_tenant,
)
from app.core.tenant.routing import (
    OPERATION_CLASS_TENANT_DATA,
    get_connection_for_tenant,
)
from app.shared.pagination import ErpPaginationParams, ErpSortParams, build_paginated_response
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.infrastructure.database.queries.inv import (
    list_almacenes,
    count_almacenes,
    get_almacen_by_id,
    get_almacen_by_codigo,
    create_almacen,
    update_almacen,
)
from app.modules.inv.application.services.inv_audit_context import apply_create_audit
from app.modules.inv.application.services.inv_codigo_generation_service import (
    InvCodigoGenerationService,
)
from app.modules.inv.presentation.schemas import (
    AlmacenCreate,
    AlmacenUpdate,
    AlmacenRead,
)

_SEQUENCE_KEY = "inv_almacen"


def _row_to_read(row: dict) -> AlmacenRead:
    return AlmacenRead(**row)


def _normalize_manual_codigo(codigo: Optional[str]) -> Optional[str]:
    if codigo is None:
        return None
    stripped = codigo.strip()
    return stripped if stripped else None


async def list_almacenes_servicio(
    client_id: UUID,
    sucursal_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    pagination: Optional[ErpPaginationParams] = None,
    sort: Optional[ErpSortParams] = None,
) -> Union[List[AlmacenRead], ErpPaginatedResponse[AlmacenRead]]:
    empresa_id = require_session_empresa_id()
    sort_by = sort.sort_by if sort else None
    sort_dir = sort.sort_dir if sort and sort.is_active else None
    filtros = dict(
        client_id=client_id,
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        solo_activos=solo_activos,
        buscar=buscar,
    )
    list_filtros = {**filtros, "sort_by": sort_by, "sort_dir": sort_dir}
    if pagination is None or not pagination.is_paginated:
        rows = await list_almacenes(**list_filtros)
        return [_row_to_read(r) for r in rows]
    total = await count_almacenes(**filtros)
    rows = await list_almacenes(**list_filtros, pagination=pagination)
    items = [_row_to_read(r) for r in rows]
    return build_paginated_response(items, total, pagination)


async def get_almacen_servicio(
    client_id: UUID,
    almacen_id: UUID,
) -> AlmacenRead:
    empresa_id = require_session_empresa_id()
    row = await get_almacen_by_id(
        client_id=client_id,
        almacen_id=almacen_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Almacén no encontrado")
    return _row_to_read(row)


async def create_almacen_servicio(
    client_id: UUID,
    data: AlmacenCreate,
    usuario_id: Optional[UUID] = None,
) -> AlmacenRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    manual_codigo = _normalize_manual_codigo(data.codigo)

    async with get_connection_for_tenant(
        client_id, OPERATION_CLASS_TENANT_DATA
    ) as session:
        async with session.begin():
            if manual_codigo:
                if await get_almacen_by_codigo(
                    client_id,
                    empresa_id,
                    manual_codigo,
                    session=session,
                ):
                    raise ConflictError(
                        detail=(
                            f"Ya existe un almacén con el código '{manual_codigo}' "
                            "en esta empresa."
                        ),
                    )

            codigo = await InvCodigoGenerationService.resolve_codigo_for_create(
                _SEQUENCE_KEY,
                session=session,
                client_id=client_id,
                empresa_id=empresa_id,
                manual_code=manual_codigo,
            )

            payload = data.model_dump()
            payload["empresa_id"] = empresa_id
            payload["codigo"] = codigo
            payload = apply_create_audit(payload, usuario_id)
            row = await create_almacen(
                client_id=client_id, data=payload, session=session
            )

    return _row_to_read(row)


async def update_almacen_servicio(
    client_id: UUID,
    almacen_id: UUID,
    data: AlmacenUpdate,
    usuario_id: Optional[UUID] = None,
) -> AlmacenRead:
    empresa_id = require_session_empresa_id()
    row = await get_almacen_by_id(
        client_id=client_id,
        almacen_id=almacen_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Almacén no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_almacen(
        client_id=client_id,
        almacen_id=almacen_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)
