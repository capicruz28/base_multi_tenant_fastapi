# app/modules/org/application/services/empresa_service.py
"""
Servicio de Empresa (ORG). Tenant-scoped: cliente_id de sesión efectiva (Etapa C1).

No usa empresa_id de sesión JWT para listar: tenant_admin ve todas las empresas del tenant.
Impersonación: client_id resuelto desde JWT (ACME), no fila platform (SYSTEM).
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.core.tenant.company_scope import assert_row_tenant
from app.core.tenant.session_scope import (
    log_org_assert_tenant,
    log_org_empresa_scope,
    log_org_tenant_scope,
)
from app.infrastructure.database.queries.org import (
    list_empresas,
    get_empresa_by_id,
    get_empresa_by_codigo,
    get_empresa_by_ruc,
    create_empresa,
    update_empresa,
)
from app.modules.org.presentation.schemas import (
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaRead,
)

_RESOURCE = "empresa"
_NOT_FOUND = "Empresa no encontrada"


def _row_to_read(row: dict) -> EmpresaRead:
    return EmpresaRead(**row)


def _assert_empresa_row(
    row: Optional[dict],
    client_id: UUID,
    empresa_id: UUID,
) -> dict:
    log_org_assert_tenant(
        resource=_RESOURCE,
        entity_id=empresa_id,
        session_client_id=client_id,
        row_cliente_id=row.get("cliente_id") if row else None,
    )
    assert_row_tenant(row, client_id, not_found_detail=_NOT_FOUND)
    return row


async def list_empresas_servicio(
    client_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> List[EmpresaRead]:
    log_org_tenant_scope(operation="list", client_id=client_id, resource=_RESOURCE)
    rows = await list_empresas(client_id=client_id, solo_activos=solo_activos)
    empresas: List[EmpresaRead] = []
    for r in rows:
        assert_row_tenant(r, client_id, not_found_detail=_NOT_FOUND)
        empresas.append(_row_to_read(r))
    if buscar:
        term = buscar.lower()
        empresas = [
            e
            for e in empresas
            if term in e.codigo_empresa.lower() or term in e.razon_social.lower()
        ]
    return empresas


async def get_empresa_servicio(
    client_id: UUID,
    empresa_id: UUID,
) -> EmpresaRead:
    """
    Verifica que la empresa exista en el tenant de sesión.
    Usado por ensure_empresa_in_tenant y endpoints ORG.
    """
    log_org_empresa_scope(operation="get", client_id=client_id, empresa_id=empresa_id)
    row = await get_empresa_by_id(client_id=client_id, empresa_id=empresa_id)
    _assert_empresa_row(row, client_id, empresa_id)
    return _row_to_read(row)


async def create_empresa_servicio(
    client_id: UUID,
    data: EmpresaCreate,
) -> EmpresaRead:
    log_org_tenant_scope(operation="create", client_id=client_id, resource=_RESOURCE)
    if await get_empresa_by_codigo(client_id, data.codigo_empresa):
        raise ConflictError(
            detail=f"Ya existe una empresa con el código '{data.codigo_empresa}' en este tenant.",
        )
    if await get_empresa_by_ruc(client_id, data.ruc):
        raise ConflictError(
            detail=f"Ya existe una empresa con el RUC '{data.ruc}' en este tenant.",
        )
    payload = data.model_dump()
    row = await create_empresa(client_id=client_id, data=payload)
    empresa_id = row["empresa_id"]
    log_org_empresa_scope(operation="create_ok", client_id=client_id, empresa_id=empresa_id)
    _assert_empresa_row(row, client_id, empresa_id)
    return _row_to_read(row)


async def update_empresa_servicio(
    client_id: UUID,
    empresa_id: UUID,
    data: EmpresaUpdate,
) -> EmpresaRead:
    log_org_empresa_scope(operation="update", client_id=client_id, empresa_id=empresa_id)
    row = await get_empresa_by_id(client_id=client_id, empresa_id=empresa_id)
    _assert_empresa_row(row, client_id, empresa_id)
    payload = data.model_dump(exclude_unset=True)
    if "codigo_empresa" in payload:
        if await get_empresa_by_codigo(
            client_id, payload["codigo_empresa"], exclude_id=empresa_id
        ):
            raise ConflictError(
                detail=f"Ya existe una empresa con el código '{payload['codigo_empresa']}' en este tenant.",
            )
    if "ruc" in payload:
        if await get_empresa_by_ruc(client_id, payload["ruc"], exclude_id=empresa_id):
            raise ConflictError(
                detail=f"Ya existe una empresa con el RUC '{payload['ruc']}' en este tenant.",
            )
    updated = await update_empresa(
        client_id=client_id, empresa_id=empresa_id, data=payload
    )
    _assert_empresa_row(updated, client_id, empresa_id)
    return _row_to_read(updated)


async def delete_empresa_servicio(
    client_id: UUID,
    empresa_id: UUID,
) -> None:
    """Baja lógica de una empresa (es_activo = False) dentro del tenant de sesión."""
    log_org_empresa_scope(operation="delete", client_id=client_id, empresa_id=empresa_id)
    row = await get_empresa_by_id(client_id=client_id, empresa_id=empresa_id)
    _assert_empresa_row(row, client_id, empresa_id)
    await update_empresa(
        client_id=client_id,
        empresa_id=empresa_id,
        data={"es_activo": False},
    )


async def reactivar_empresa_servicio(
    client_id: UUID,
    empresa_id: UUID,
) -> EmpresaRead:
    log_org_empresa_scope(operation="reactivate", client_id=client_id, empresa_id=empresa_id)
    row = await get_empresa_by_id(client_id=client_id, empresa_id=empresa_id)
    _assert_empresa_row(row, client_id, empresa_id)
    updated = await update_empresa(
        client_id=client_id,
        empresa_id=empresa_id,
        data={"es_activo": True},
    )
    _assert_empresa_row(updated, client_id, empresa_id)
    return _row_to_read(updated)
