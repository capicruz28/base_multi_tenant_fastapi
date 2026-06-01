# app/modules/org/application/services/centro_costo_service.py
"""Servicio de Centro de Costo (ORG). Aislamiento multi-empresa: empresa_id desde sesión JWT."""
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
from app.infrastructure.database.queries.org import (
    list_centros_costo,
    get_centro_costo_by_id,
    get_centro_costo_by_codigo,
    create_centro_costo,
    update_centro_costo,
)
from app.modules.org.presentation.schemas import (
    CentroCostoCreate,
    CentroCostoUpdate,
    CentroCostoRead,
)

_RESOURCE = "centro_costo"
_NOT_FOUND = "Centro de costo no encontrado"


def _row_to_read(row: dict) -> CentroCostoRead:
    return CentroCostoRead(**row)


def _session_empresa(operation: str) -> UUID:
    empresa_id = require_session_empresa_id()
    log_org_session_empresa(operation=operation, empresa_id=empresa_id, resource=_RESOURCE)
    return empresa_id


async def list_centros_costo_servicio(
    client_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> List[CentroCostoRead]:
    empresa_id = _session_empresa("list")
    log_org_company_scope(
        operation="list",
        client_id=client_id,
        session_empresa_id=empresa_id,
        resource=_RESOURCE,
    )
    rows = await list_centros_costo(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )
    centros = [_row_to_read(r) for r in rows]
    if buscar:
        term = buscar.lower()
        centros = [
            c
            for c in centros
            if term in (c.codigo or "").lower() or term in (c.nombre or "").lower()
        ]
    return centros


async def get_centro_costo_servicio(
    client_id: UUID,
    centro_costo_id: UUID,
) -> CentroCostoRead:
    empresa_id = _session_empresa("get")
    row = await get_centro_costo_by_id(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        empresa_id=empresa_id,
    )
    log_org_assert_empresa(
        resource=_RESOURCE,
        entity_id=centro_costo_id,
        session_empresa_id=empresa_id,
        row_empresa_id=row.get("empresa_id") if row else None,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(row)


async def create_centro_costo_servicio(
    client_id: UUID,
    data: CentroCostoCreate,
) -> CentroCostoRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    log_org_company_scope(
        operation="create",
        client_id=client_id,
        session_empresa_id=empresa_id,
        resource=_RESOURCE,
    )
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    if await get_centro_costo_by_codigo(client_id, empresa_id, data.codigo):
        raise ConflictError(
            detail=f"Ya existe un centro de costo con el código '{data.codigo}' en esta empresa.",
        )
    payload = data.model_dump()
    payload["empresa_id"] = empresa_id
    row = await create_centro_costo(client_id=client_id, data=payload)
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(row)


async def update_centro_costo_servicio(
    client_id: UUID,
    centro_costo_id: UUID,
    data: CentroCostoUpdate,
) -> CentroCostoRead:
    empresa_id = _session_empresa("update")
    row = await get_centro_costo_by_id(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        empresa_id=empresa_id,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    payload = data.model_dump(exclude_unset=True)
    if "codigo" in payload:
        if await get_centro_costo_by_codigo(
            client_id, empresa_id, payload["codigo"], exclude_id=centro_costo_id
        ):
            raise ConflictError(
                detail=f"Ya existe un centro de costo con el código '{payload['codigo']}' en esta empresa.",
            )
    updated = await update_centro_costo(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        data=payload,
        empresa_id=empresa_id,
    )
    assert_row_empresa(updated, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(updated)


async def delete_centro_costo_servicio(
    client_id: UUID,
    centro_costo_id: UUID,
) -> None:
    empresa_id = _session_empresa("delete")
    row = await get_centro_costo_by_id(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        empresa_id=empresa_id,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    await update_centro_costo(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        data={"es_activo": False},
        empresa_id=empresa_id,
    )


async def reactivar_centro_costo_servicio(
    client_id: UUID,
    centro_costo_id: UUID,
) -> CentroCostoRead:
    empresa_id = _session_empresa("reactivate")
    row = await get_centro_costo_by_id(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        empresa_id=empresa_id,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    updated = await update_centro_costo(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        data={"es_activo": True},
        empresa_id=empresa_id,
    )
    assert_row_empresa(updated, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(updated)
