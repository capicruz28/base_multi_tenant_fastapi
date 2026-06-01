# app/modules/org/application/services/cargo_service.py
"""Servicio de Cargo (ORG). Aislamiento multi-empresa: empresa_id desde sesión JWT."""
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
    list_cargos,
    get_cargo_by_id,
    get_cargo_by_codigo,
    create_cargo,
    update_cargo,
)
from app.modules.org.presentation.schemas import CargoCreate, CargoUpdate, CargoRead

_RESOURCE = "cargo"
_NOT_FOUND = "Cargo no encontrado"


def _row_to_read(row: dict) -> CargoRead:
    return CargoRead(**row)


def _session_empresa(operation: str) -> UUID:
    empresa_id = require_session_empresa_id()
    log_org_session_empresa(operation=operation, empresa_id=empresa_id, resource=_RESOURCE)
    return empresa_id


async def list_cargos_servicio(
    client_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> List[CargoRead]:
    empresa_id = _session_empresa("list")
    log_org_company_scope(
        operation="list",
        client_id=client_id,
        session_empresa_id=empresa_id,
        resource=_RESOURCE,
    )
    rows = await list_cargos(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )
    cargos = [_row_to_read(r) for r in rows]
    if buscar:
        term = buscar.lower()
        cargos = [
            c
            for c in cargos
            if term in (c.codigo or "").lower() or term in (c.nombre or "").lower()
        ]
    return cargos


async def get_cargo_servicio(
    client_id: UUID,
    cargo_id: UUID,
) -> CargoRead:
    empresa_id = _session_empresa("get")
    row = await get_cargo_by_id(
        client_id=client_id,
        cargo_id=cargo_id,
        empresa_id=empresa_id,
    )
    log_org_assert_empresa(
        resource=_RESOURCE,
        entity_id=cargo_id,
        session_empresa_id=empresa_id,
        row_empresa_id=row.get("empresa_id") if row else None,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(row)


async def create_cargo_servicio(
    client_id: UUID,
    data: CargoCreate,
) -> CargoRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    log_org_company_scope(
        operation="create",
        client_id=client_id,
        session_empresa_id=empresa_id,
        resource=_RESOURCE,
    )
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    if await get_cargo_by_codigo(client_id, empresa_id, data.codigo):
        raise ConflictError(
            detail=f"Ya existe un cargo con el código '{data.codigo}' en esta empresa.",
        )
    payload = data.model_dump()
    payload["empresa_id"] = empresa_id
    row = await create_cargo(client_id=client_id, data=payload)
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(row)


async def update_cargo_servicio(
    client_id: UUID,
    cargo_id: UUID,
    data: CargoUpdate,
) -> CargoRead:
    empresa_id = _session_empresa("update")
    row = await get_cargo_by_id(
        client_id=client_id,
        cargo_id=cargo_id,
        empresa_id=empresa_id,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    payload = data.model_dump(exclude_unset=True)
    if "codigo" in payload:
        if await get_cargo_by_codigo(
            client_id, empresa_id, payload["codigo"], exclude_id=cargo_id
        ):
            raise ConflictError(
                detail=f"Ya existe un cargo con el código '{payload['codigo']}' en esta empresa.",
            )
    updated = await update_cargo(
        client_id=client_id,
        cargo_id=cargo_id,
        data=payload,
        empresa_id=empresa_id,
    )
    assert_row_empresa(updated, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(updated)


async def delete_cargo_servicio(
    client_id: UUID,
    cargo_id: UUID,
) -> None:
    empresa_id = _session_empresa("delete")
    row = await get_cargo_by_id(
        client_id=client_id,
        cargo_id=cargo_id,
        empresa_id=empresa_id,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    await update_cargo(
        client_id=client_id,
        cargo_id=cargo_id,
        data={"es_activo": False},
        empresa_id=empresa_id,
    )


async def reactivar_cargo_servicio(
    client_id: UUID,
    cargo_id: UUID,
) -> CargoRead:
    empresa_id = _session_empresa("reactivate")
    row = await get_cargo_by_id(
        client_id=client_id,
        cargo_id=cargo_id,
        empresa_id=empresa_id,
    )
    assert_row_empresa(row, empresa_id, not_found_detail=_NOT_FOUND)
    updated = await update_cargo(
        client_id=client_id,
        cargo_id=cargo_id,
        data={"es_activo": True},
        empresa_id=empresa_id,
    )
    assert_row_empresa(updated, empresa_id, not_found_detail=_NOT_FOUND)
    return _row_to_read(updated)
