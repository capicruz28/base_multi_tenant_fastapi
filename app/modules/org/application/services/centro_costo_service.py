# app/modules/org/application/services/centro_costo_service.py
"""Servicio de Centro de Costo (ORG). client_id desde contexto."""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.queries.org import (
    list_centros_costo,
    get_centro_costo_by_id,
    create_centro_costo,
    update_centro_costo,
)
from app.modules.org.presentation.schemas import (
    CentroCostoCreate,
    CentroCostoUpdate,
    CentroCostoRead,
)


def _row_to_read(row: dict) -> CentroCostoRead:
    return CentroCostoRead(**row)

def _require_empresa_id(empresa_id: Optional[UUID]) -> UUID:
    if empresa_id is None:
        raise ValidationError(
            detail="empresa_id es obligatorio para operar centros de costo por ID.",
            internal_code="MISSING_REQUIRED_FIELDS",
        )
    return empresa_id


async def list_centros_costo_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> List[CentroCostoRead]:
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
    empresa_id: Optional[UUID] = None,
) -> CentroCostoRead:
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_centro_costo_by_id(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Centro de costo no encontrado")
    return _row_to_read(row)


async def create_centro_costo_servicio(
    client_id: UUID,
    data: CentroCostoCreate,
) -> CentroCostoRead:
    payload = data.model_dump()
    row = await create_centro_costo(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_centro_costo_servicio(
    client_id: UUID,
    centro_costo_id: UUID,
    data: CentroCostoUpdate,
    empresa_id: Optional[UUID] = None,
) -> CentroCostoRead:
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_centro_costo_by_id(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Centro de costo no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_centro_costo(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)


async def delete_centro_costo_servicio(
    client_id: UUID,
    centro_costo_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> None:
    """
    Baja lógica de un centro de costo (es_activo = False).
    """
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_centro_costo_by_id(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Centro de costo no encontrado")
    await update_centro_costo(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        data={"es_activo": False},
        empresa_id=empresa_id,
    )


async def reactivar_centro_costo_servicio(
    client_id: UUID,
    centro_costo_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> CentroCostoRead:
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_centro_costo_by_id(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Centro de costo no encontrado")
    updated = await update_centro_costo(
        client_id=client_id,
        centro_costo_id=centro_costo_id,
        data={"es_activo": True},
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)
