# app/modules/org/application/services/departamento_service.py
"""Servicio de Departamento (ORG). Aislamiento multi-empresa: empresa_id desde sesión JWT."""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.core.tenant.company_scope import (
    assert_row_empresa,
    enforce_body_empresa_matches_session,
    ensure_empresa_in_tenant,
    require_session_empresa_id,
)
from app.core.tenant.session_scope import (
    log_org_assert_empresa,
    log_org_company_scope,
    log_org_session_empresa,
)
from app.shared.pagination import ErpSortParams
from app.infrastructure.database.queries.org import (
    list_departamentos,
    get_departamento_by_id,
    get_departamento_by_codigo,
    create_departamento,
    update_departamento,
)
from app.modules.org.presentation.schemas import (
    DepartamentoCreate,
    DepartamentoUpdate,
    DepartamentoRead,
)

_RESOURCE = "departamento"
_NOT_FOUND = "Departamento no encontrado"


def _row_to_read(row: dict) -> DepartamentoRead:
    return DepartamentoRead(**row)


def _session_empresa(operation: str) -> UUID:
    empresa_id = require_session_empresa_id()
    log_org_session_empresa(operation=operation, empresa_id=empresa_id, resource=_RESOURCE)
    return empresa_id


async def list_departamentos_servicio(
    client_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    sort: Optional[ErpSortParams] = None,
) -> List[DepartamentoRead]:
    empresa_id = _session_empresa("list")
    log_org_company_scope(
        operation="list",
        client_id=client_id,
        session_empresa_id=empresa_id,
        resource=_RESOURCE,
    )
    sort_by = sort.sort_by if sort else None
    sort_dir = sort.sort_dir if sort and sort.is_active else None
    rows = await list_departamentos(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
        buscar=buscar,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return [_row_to_read(r) for r in rows]


async def get_departamento_servicio(
    client_id: UUID,
    departamento_id: UUID,
) -> DepartamentoRead:
    empresa_id = _session_empresa("get")
    row = await get_departamento_by_id(
        client_id=client_id,
        departamento_id=departamento_id,
        empresa_id=empresa_id,
    )
    log_org_assert_empresa(
        resource=_RESOURCE,
        entity_id=departamento_id,
        session_empresa_id=empresa_id,
        row_empresa_id=row.get("empresa_id") if row else None,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(row)


async def create_departamento_servicio(
    client_id: UUID,
    data: DepartamentoCreate,
) -> DepartamentoRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    log_org_company_scope(
        operation="create",
        client_id=client_id,
        session_empresa_id=empresa_id,
        resource=_RESOURCE,
    )
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    if await get_departamento_by_codigo(client_id, empresa_id, data.codigo):
        raise ConflictError(
            detail=f"Ya existe un departamento con el código '{data.codigo}' en esta empresa.",
        )
    payload = data.model_dump()
    payload["empresa_id"] = empresa_id
    row = await create_departamento(client_id=client_id, data=payload)
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(row)


async def update_departamento_servicio(
    client_id: UUID,
    departamento_id: UUID,
    data: DepartamentoUpdate,
) -> DepartamentoRead:
    empresa_id = _session_empresa("update")
    row = await get_departamento_by_id(
        client_id=client_id,
        departamento_id=departamento_id,
        empresa_id=empresa_id,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    payload = data.model_dump(exclude_unset=True)
    if "codigo" in payload:
        if await get_departamento_by_codigo(
            client_id, empresa_id, payload["codigo"], exclude_id=departamento_id
        ):
            raise ConflictError(
                detail=f"Ya existe un departamento con el código '{payload['codigo']}' en esta empresa.",
            )
    updated = await update_departamento(
        client_id=client_id,
        departamento_id=departamento_id,
        data=payload,
        empresa_id=empresa_id,
    )
    assert_row_empresa(updated, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(updated)


async def delete_departamento_servicio(
    client_id: UUID,
    departamento_id: UUID,
) -> None:
    empresa_id = _session_empresa("delete")
    row = await get_departamento_by_id(
        client_id=client_id,
        departamento_id=departamento_id,
        empresa_id=empresa_id,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    await update_departamento(
        client_id=client_id,
        departamento_id=departamento_id,
        data={"es_activo": False},
        empresa_id=empresa_id,
    )


async def reactivar_departamento_servicio(
    client_id: UUID,
    departamento_id: UUID,
) -> DepartamentoRead:
    empresa_id = _session_empresa("reactivate")
    row = await get_departamento_by_id(
        client_id=client_id,
        departamento_id=departamento_id,
        empresa_id=empresa_id,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    updated = await update_departamento(
        client_id=client_id,
        departamento_id=departamento_id,
        data={"es_activo": True},
        empresa_id=empresa_id,
    )
    assert_row_empresa(updated, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(updated)
