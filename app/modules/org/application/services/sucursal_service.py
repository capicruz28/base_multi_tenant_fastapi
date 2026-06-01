# app/modules/org/application/services/sucursal_service.py
"""
Servicio de Sucursal (ORG). Aislamiento multi-empresa: empresa_id desde sesión JWT.
"""
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
    list_sucursales,
    get_sucursal_by_id,
    get_sucursal_by_codigo,
    create_sucursal,
    update_sucursal,
)
from app.modules.org.presentation.schemas import (
    SucursalCreate,
    SucursalUpdate,
    SucursalRead,
)

_RESOURCE = "sucursal"
_NOT_FOUND = "Sucursal no encontrada"


def _row_to_read(row: dict) -> SucursalRead:
    return SucursalRead(**row)


def _session_empresa(operation: str) -> UUID:
    empresa_id = require_session_empresa_id()
    log_org_session_empresa(operation=operation, empresa_id=empresa_id, resource=_RESOURCE)
    return empresa_id


async def list_sucursales_servicio(
    client_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> List[SucursalRead]:
    empresa_id = _session_empresa("list")
    log_org_company_scope(
        operation="list",
        client_id=client_id,
        session_empresa_id=empresa_id,
        resource=_RESOURCE,
    )
    rows = await list_sucursales(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )
    sucursales = [_row_to_read(r) for r in rows]
    if buscar:
        term = buscar.lower()
        sucursales = [
            s
            for s in sucursales
            if term in (s.codigo or "").lower() or term in (s.nombre or "").lower()
        ]
    return sucursales


async def get_sucursal_servicio(
    client_id: UUID,
    sucursal_id: UUID,
) -> SucursalRead:
    empresa_id = _session_empresa("get")
    row = await get_sucursal_by_id(
        client_id=client_id,
        sucursal_id=sucursal_id,
        empresa_id=empresa_id,
    )
    log_org_assert_empresa(
        resource=_RESOURCE,
        entity_id=sucursal_id,
        session_empresa_id=empresa_id,
        row_empresa_id=row.get("empresa_id") if row else None,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(row)


async def create_sucursal_servicio(
    client_id: UUID,
    data: SucursalCreate,
) -> SucursalRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    log_org_company_scope(
        operation="create",
        client_id=client_id,
        session_empresa_id=empresa_id,
        resource=_RESOURCE,
    )
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    if await get_sucursal_by_codigo(client_id, empresa_id, data.codigo):
        raise ConflictError(
            detail=f"Ya existe una sucursal con el código '{data.codigo}' en esta empresa.",
        )
    payload = data.model_dump()
    payload["empresa_id"] = empresa_id
    row = await create_sucursal(client_id=client_id, data=payload)
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(row)


async def update_sucursal_servicio(
    client_id: UUID,
    sucursal_id: UUID,
    data: SucursalUpdate,
) -> SucursalRead:
    empresa_id = _session_empresa("update")
    row = await get_sucursal_by_id(
        client_id=client_id,
        sucursal_id=sucursal_id,
        empresa_id=empresa_id,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    payload = data.model_dump(exclude_unset=True)
    if "codigo" in payload:
        if await get_sucursal_by_codigo(
            client_id, empresa_id, payload["codigo"], exclude_id=sucursal_id
        ):
            raise ConflictError(
                detail=f"Ya existe una sucursal con el código '{payload['codigo']}' en esta empresa.",
            )
    updated = await update_sucursal(
        client_id=client_id,
        sucursal_id=sucursal_id,
        data=payload,
        empresa_id=empresa_id,
    )
    assert_row_empresa(updated, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(updated)


async def delete_sucursal_servicio(
    client_id: UUID,
    sucursal_id: UUID,
) -> None:
    """Baja lógica de una sucursal (es_activo = False)."""
    empresa_id = _session_empresa("delete")
    row = await get_sucursal_by_id(
        client_id=client_id,
        sucursal_id=sucursal_id,
        empresa_id=empresa_id,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    await update_sucursal(
        client_id=client_id,
        sucursal_id=sucursal_id,
        data={"es_activo": False},
        empresa_id=empresa_id,
    )


async def reactivar_sucursal_servicio(
    client_id: UUID,
    sucursal_id: UUID,
) -> SucursalRead:
    empresa_id = _session_empresa("reactivate")
    row = await get_sucursal_by_id(
        client_id=client_id,
        sucursal_id=sucursal_id,
        empresa_id=empresa_id,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    updated = await update_sucursal(
        client_id=client_id,
        sucursal_id=sucursal_id,
        data={"es_activo": True},
        empresa_id=empresa_id,
    )
    assert_row_empresa(updated, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(updated)
