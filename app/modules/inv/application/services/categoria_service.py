# app/modules/inv/application/services/categoria_service.py
"""
Servicio de Categoría de Producto (INV). client_id siempre desde contexto, nunca desde body.
Aislamiento multi-empresa: empresa_id desde sesión JWT (company_scope).
CREATE: UoW + InvCodigoGenerationService (sequence_key inv_categoria_producto).
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
    list_categorias,
    count_categorias,
    get_categoria_by_id,
    get_categoria_by_codigo,
    create_categoria,
    update_categoria,
)
from app.modules.inv.application.services.inv_audit_context import apply_create_audit
from app.modules.inv.application.services.inv_codigo_generation_service import (
    InvCodigoGenerationService,
)
from app.modules.inv.presentation.schemas import (
    CategoriaCreate,
    CategoriaUpdate,
    CategoriaRead,
)

_SEQUENCE_KEY = "inv_categoria_producto"


def _row_to_read(row: dict) -> CategoriaRead:
    return CategoriaRead(**row)


def _normalize_manual_codigo(codigo: Optional[str]) -> Optional[str]:
    if codigo is None:
        return None
    stripped = codigo.strip()
    return stripped if stripped else None


async def list_categorias_servicio(
    client_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    pagination: Optional[ErpPaginationParams] = None,
    sort: Optional[ErpSortParams] = None,
) -> Union[List[CategoriaRead], ErpPaginatedResponse[CategoriaRead]]:
    empresa_id = require_session_empresa_id()
    sort_by = sort.sort_by if sort else None
    sort_dir = sort.sort_dir if sort and sort.is_active else None
    filtros = dict(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
        buscar=buscar,
    )
    list_filtros = {**filtros, "sort_by": sort_by, "sort_dir": sort_dir}
    if pagination is None or not pagination.is_paginated:
        rows = await list_categorias(**list_filtros)
        return [_row_to_read(r) for r in rows]
    total = await count_categorias(**filtros)
    rows = await list_categorias(**list_filtros, pagination=pagination)
    items = [_row_to_read(r) for r in rows]
    return build_paginated_response(items, total, pagination)


async def get_categoria_servicio(
    client_id: UUID,
    categoria_id: UUID,
) -> CategoriaRead:
    empresa_id = require_session_empresa_id()
    row = await get_categoria_by_id(
        client_id=client_id,
        categoria_id=categoria_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Categoría no encontrada")
    return _row_to_read(row)


async def create_categoria_servicio(
    client_id: UUID,
    data: CategoriaCreate,
    usuario_id: Optional[UUID] = None,
) -> CategoriaRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    manual_codigo = _normalize_manual_codigo(data.codigo)

    async with get_connection_for_tenant(
        client_id, OPERATION_CLASS_TENANT_DATA
    ) as session:
        async with session.begin():
            if manual_codigo:
                if await get_categoria_by_codigo(
                    client_id,
                    empresa_id,
                    manual_codigo,
                    session=session,
                ):
                    raise ConflictError(
                        detail=(
                            f"Ya existe una categoría con el código '{manual_codigo}' "
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
            row = await create_categoria(
                client_id=client_id, data=payload, session=session
            )

    return _row_to_read(row)


async def update_categoria_servicio(
    client_id: UUID,
    categoria_id: UUID,
    data: CategoriaUpdate,
    usuario_id: Optional[UUID] = None,
) -> CategoriaRead:
    empresa_id = require_session_empresa_id()
    row = await get_categoria_by_id(
        client_id=client_id,
        categoria_id=categoria_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Categoría no encontrada")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_categoria(
        client_id=client_id,
        categoria_id=categoria_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)
