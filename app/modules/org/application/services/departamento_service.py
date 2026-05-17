# app/modules/org/application/services/departamento_service.py
"""Servicio de Departamento (ORG). client_id desde contexto."""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
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


def _row_to_read(row: dict) -> DepartamentoRead:
    return DepartamentoRead(**row)

def _require_empresa_id(empresa_id: Optional[UUID]) -> UUID:
    if empresa_id is None:
        raise ValidationError(
            detail="empresa_id es obligatorio para operar departamentos por ID.",
            internal_code="MISSING_REQUIRED_FIELDS",
        )
    return empresa_id


async def list_departamentos_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> List[DepartamentoRead]:
    rows = await list_departamentos(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )
    departamentos = [_row_to_read(r) for r in rows]
    if buscar:
        term = buscar.lower()
        departamentos = [
            d
            for d in departamentos
            if term in (d.codigo or "").lower() or term in (d.nombre or "").lower()
        ]
    return departamentos


async def get_departamento_servicio(
    client_id: UUID,
    departamento_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> DepartamentoRead:
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_departamento_by_id(
        client_id=client_id,
        departamento_id=departamento_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Departamento no encontrado")
    return _row_to_read(row)


async def create_departamento_servicio(
    client_id: UUID,
    data: DepartamentoCreate,
) -> DepartamentoRead:
    if await get_departamento_by_codigo(client_id, data.empresa_id, data.codigo):
        raise ConflictError(
            detail=f"Ya existe un departamento con el código '{data.codigo}' en esta empresa.",
        )
    payload = data.model_dump()
    row = await create_departamento(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_departamento_servicio(
    client_id: UUID,
    departamento_id: UUID,
    data: DepartamentoUpdate,
    empresa_id: Optional[UUID] = None,
) -> DepartamentoRead:
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_departamento_by_id(
        client_id=client_id,
        departamento_id=departamento_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Departamento no encontrado")
    payload = data.model_dump(exclude_unset=True)
    if "codigo" in payload:
        if await get_departamento_by_codigo(client_id, empresa_id, payload["codigo"], exclude_id=departamento_id):
            raise ConflictError(
                detail=f"Ya existe un departamento con el código '{payload['codigo']}' en esta empresa.",
            )
    updated = await update_departamento(
        client_id=client_id,
        departamento_id=departamento_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)


async def delete_departamento_servicio(
    client_id: UUID,
    departamento_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> None:
    """
    Baja lógica de un departamento (es_activo = False).
    """
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_departamento_by_id(
        client_id=client_id,
        departamento_id=departamento_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Departamento no encontrado")
    await update_departamento(
        client_id=client_id,
        departamento_id=departamento_id,
        data={"es_activo": False},
        empresa_id=empresa_id,
    )


async def reactivar_departamento_servicio(
    client_id: UUID,
    departamento_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> DepartamentoRead:
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_departamento_by_id(
        client_id=client_id,
        departamento_id=departamento_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Departamento no encontrado")
    updated = await update_departamento(
        client_id=client_id,
        departamento_id=departamento_id,
        data={"es_activo": True},
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)
