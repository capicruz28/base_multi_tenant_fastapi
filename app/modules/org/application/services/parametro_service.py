# app/modules/org/application/services/parametro_service.py
"""
Servicio de Parámetro Sistema (ORG). Ámbito HYBRID (Etapa C2).

Lectura ERP: globales tenant (empresa_id NULL) + overrides empresa sesión con precedencia.
Escritura global: tenant_admin / platform. Escritura empresa: empresa_id = sesión JWT.
"""
from typing import List, Optional, Union
from uuid import UUID

from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError
from app.core.tenant.company_scope import (
    assert_row_empresa,
    assert_row_tenant,
    enforce_body_empresa_matches_session,
    require_session_empresa_id,
)
from app.core.tenant.empresa_context import coerce_empresa_id
from app.core.tenant.session_scope import (
    log_org_assert_empresa,
    log_org_assert_tenant,
    log_org_hybrid_scope,
    log_org_param_empresa,
    log_org_param_global,
    log_org_param_precedence,
)
from app.shared.pagination import ErpPaginationParams, ErpSortParams, build_paginated_response
from app.shared.pagination.query_helpers import apply_memory_sort
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.infrastructure.database.queries.org.parametro_queries import (
    apply_parametro_precedence,
    create_parametro,
    get_parametro_by_clave_natural,
    get_parametro_by_id_raw,
    list_parametros_hybrid,
    update_parametro,
)
from app.modules.org.presentation.schemas import (
    ParametroCreate,
    ParametroUpdate,
    ParametroRead,
)

_RESOURCE = "parametro"
_NOT_FOUND = "Parámetro no encontrado"
_SORT_COLUMNS_PARAMETRO = frozenset(
    {"modulo_codigo", "codigo_parametro", "nombre_parametro", "fecha_creacion", "fecha_actualizacion"}
)


def _row_to_read(row: dict) -> ParametroRead:
    return ParametroRead(**row)


def _is_global_row(row: dict) -> bool:
    return coerce_empresa_id(row.get("empresa_id")) is None


def _assert_parametro_visible_for_erp_read(
    row: Optional[dict],
    client_id: UUID,
    session_empresa_id: UUID,
    parametro_id: UUID,
) -> dict:
    """Fila visible en lectura híbrida: global tenant o override de empresa sesión."""
    log_org_assert_tenant(
        resource=_RESOURCE,
        entity_id=parametro_id,
        session_client_id=client_id,
        row_cliente_id=row.get("cliente_id") if row else None,
    )
    assert_row_tenant(row, client_id, not_found_detail=_NOT_FOUND)
    if row is None:
        raise NotFoundError(detail=_NOT_FOUND)
    row_empresa = coerce_empresa_id(row.get("empresa_id"))
    if row_empresa is not None:
        log_org_assert_empresa(
            resource=_RESOURCE,
            entity_id=parametro_id,
            session_empresa_id=session_empresa_id,
            row_empresa_id=row_empresa,
        )
        assert_row_empresa(row, session_empresa_id, not_found_detail=_NOT_FOUND)
    return row


def _assert_can_mutate_row(
    row: dict,
    *,
    can_manage_global: bool,
    session_empresa_id: UUID,
) -> None:
    if _is_global_row(row):
        if not can_manage_global:
            raise AuthorizationError(
                detail="Solo un administrador del tenant puede modificar parámetros globales.",
                internal_code="GLOBAL_PARAM_FORBIDDEN",
            )
    else:
        assert_row_empresa(row, session_empresa_id, not_found_detail=_NOT_FOUND)


async def list_parametros_servicio(
    client_id: UUID,
    modulo_codigo: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    pagination: Optional[ErpPaginationParams] = None,
    sort: Optional[ErpSortParams] = None,
) -> Union[List[ParametroRead], ErpPaginatedResponse[ParametroRead]]:
    session_empresa_id = require_session_empresa_id()
    sort_by = sort.sort_by if sort else None
    sort_dir = sort.sort_dir if sort and sort.is_active else None
    rows = await list_parametros_hybrid(
        client_id=client_id,
        session_empresa_id=session_empresa_id,
        modulo_codigo=modulo_codigo,
        solo_activos=solo_activos,
        buscar=buscar,
    )
    log_org_hybrid_scope(
        operation="list_raw",
        client_id=client_id,
        session_empresa_id=session_empresa_id,
        row_count=len(rows),
    )
    merged, override_count, global_count = apply_parametro_precedence(
        rows, session_empresa_id
    )
    log_org_param_precedence(
        merged_count=len(merged),
        override_count=override_count,
        global_count=global_count,
    )
    merged = apply_memory_sort(
        merged,
        allowed_columns=_SORT_COLUMNS_PARAMETRO,
        sort_by=sort_by,
        sort_dir=sort_dir,
        default_key=lambda r: (r.get("modulo_codigo"), r.get("codigo_parametro")),
        tie_breaker_key=lambda r: str(r.get("parametro_id")),
    )
    total = len(merged)
    if pagination is None or not pagination.is_paginated:
        return [_row_to_read(r) for r in merged]
    start = pagination.offset
    end = start + pagination.limit
    page_rows = merged[start:end]
    items = [_row_to_read(r) for r in page_rows]
    return build_paginated_response(items, total, pagination)


async def get_parametro_servicio(
    client_id: UUID,
    parametro_id: UUID,
) -> ParametroRead:
    session_empresa_id = require_session_empresa_id()
    row = await get_parametro_by_id_raw(client_id=client_id, parametro_id=parametro_id)
    row = _assert_parametro_visible_for_erp_read(
        row, client_id, session_empresa_id, parametro_id
    )
    return _row_to_read(row)


async def create_parametro_servicio(
    client_id: UUID,
    data: ParametroCreate,
    *,
    can_manage_global: bool = False,
) -> ParametroRead:
    body_empresa = coerce_empresa_id(data.empresa_id)
    if body_empresa is None:
        if not can_manage_global:
            raise AuthorizationError(
                detail="Solo un administrador del tenant puede crear parámetros globales.",
                internal_code="GLOBAL_PARAM_FORBIDDEN",
            )
        log_org_param_global(operation="create", client_id=client_id)
        target_empresa_id = None
    else:
        target_empresa_id = enforce_body_empresa_matches_session(body_empresa)
        log_org_param_empresa(
            operation="create",
            client_id=client_id,
            empresa_id=target_empresa_id,
        )

    if await get_parametro_by_clave_natural(
        client_id,
        modulo_codigo=data.modulo_codigo,
        codigo_parametro=data.codigo_parametro,
        empresa_id=target_empresa_id,
    ):
        scope = "esta empresa" if target_empresa_id else "todo el tenant (global)"
        raise ConflictError(
            detail=(
                f"Ya existe un parámetro con el código '{data.codigo_parametro}' "
                f"en el módulo '{data.modulo_codigo}' para {scope}."
            ),
        )

    payload = data.model_dump()
    payload["empresa_id"] = target_empresa_id
    row = await create_parametro(client_id=client_id, data=payload)
    assert_row_tenant(row, client_id, not_found_detail=_NOT_FOUND)
    if target_empresa_id is not None:
        assert_row_empresa(row, target_empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(row)


async def update_parametro_servicio(
    client_id: UUID,
    parametro_id: UUID,
    data: ParametroUpdate,
    *,
    can_manage_global: bool = False,
) -> ParametroRead:
    session_empresa_id = require_session_empresa_id()
    row = await get_parametro_by_id_raw(client_id=client_id, parametro_id=parametro_id)
    row = _assert_parametro_visible_for_erp_read(
        row, client_id, session_empresa_id, parametro_id
    )
    _assert_can_mutate_row(
        row,
        can_manage_global=can_manage_global,
        session_empresa_id=session_empresa_id,
    )
    row_empresa_id = coerce_empresa_id(row.get("empresa_id"))
    payload = data.model_dump(exclude_unset=True)
    updated = await update_parametro(
        client_id=client_id,
        parametro_id=parametro_id,
        data=payload,
        row_empresa_id=row_empresa_id,
    )
    assert_row_tenant(updated, client_id, not_found_detail=_NOT_FOUND)
    if row_empresa_id is not None:
        assert_row_empresa(updated, session_empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(updated)


async def delete_parametro_servicio(
    client_id: UUID,
    parametro_id: UUID,
    *,
    can_manage_global: bool = False,
) -> None:
    session_empresa_id = require_session_empresa_id()
    row = await get_parametro_by_id_raw(client_id=client_id, parametro_id=parametro_id)
    row = _assert_parametro_visible_for_erp_read(
        row, client_id, session_empresa_id, parametro_id
    )
    _assert_can_mutate_row(
        row,
        can_manage_global=can_manage_global,
        session_empresa_id=session_empresa_id,
    )
    row_empresa_id = coerce_empresa_id(row.get("empresa_id"))
    await update_parametro(
        client_id=client_id,
        parametro_id=parametro_id,
        data={"es_activo": False},
        row_empresa_id=row_empresa_id,
    )


async def reactivar_parametro_servicio(
    client_id: UUID,
    parametro_id: UUID,
    *,
    can_manage_global: bool = False,
) -> ParametroRead:
    session_empresa_id = require_session_empresa_id()
    row = await get_parametro_by_id_raw(client_id=client_id, parametro_id=parametro_id)
    row = _assert_parametro_visible_for_erp_read(
        row, client_id, session_empresa_id, parametro_id
    )
    _assert_can_mutate_row(
        row,
        can_manage_global=can_manage_global,
        session_empresa_id=session_empresa_id,
    )
    row_empresa_id = coerce_empresa_id(row.get("empresa_id"))
    updated = await update_parametro(
        client_id=client_id,
        parametro_id=parametro_id,
        data={"es_activo": True},
        row_empresa_id=row_empresa_id,
    )
    assert_row_tenant(updated, client_id, not_found_detail=_NOT_FOUND)
    if row_empresa_id is not None:
        assert_row_empresa(updated, session_empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(updated)
