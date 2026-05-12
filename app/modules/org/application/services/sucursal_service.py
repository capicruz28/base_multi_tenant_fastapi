# app/modules/org/application/services/sucursal_service.py
"""Servicio de Sucursal (ORG). client_id desde contexto."""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.queries.org import (
    list_sucursales,
    get_sucursal_by_id,
    create_sucursal,
    update_sucursal,
)
from app.modules.org.presentation.schemas import (
    SucursalCreate,
    SucursalUpdate,
    SucursalRead,
)


def _row_to_read(row: dict) -> SucursalRead:
    return SucursalRead(**row)

def _require_empresa_id(empresa_id: Optional[UUID]) -> UUID:
    if empresa_id is None:
        raise ValidationError(
            detail="empresa_id es obligatorio para operar sucursales por ID.",
            internal_code="MISSING_REQUIRED_FIELDS",
        )
    return empresa_id


async def list_sucursales_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> List[SucursalRead]:
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
    empresa_id: Optional[UUID] = None,
) -> SucursalRead:
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_sucursal_by_id(
        client_id=client_id,
        sucursal_id=sucursal_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Sucursal no encontrada")
    return _row_to_read(row)


async def create_sucursal_servicio(
    client_id: UUID,
    data: SucursalCreate,
) -> SucursalRead:
    payload = data.model_dump()
    row = await create_sucursal(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_sucursal_servicio(
    client_id: UUID,
    sucursal_id: UUID,
    data: SucursalUpdate,
    empresa_id: Optional[UUID] = None,
) -> SucursalRead:
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_sucursal_by_id(
        client_id=client_id,
        sucursal_id=sucursal_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Sucursal no encontrada")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_sucursal(
        client_id=client_id,
        sucursal_id=sucursal_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)


async def delete_sucursal_servicio(
    client_id: UUID,
    sucursal_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> None:
    """
    Baja lógica de una sucursal (es_activo = False).
    """
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_sucursal_by_id(
        client_id=client_id,
        sucursal_id=sucursal_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Sucursal no encontrada")
    await update_sucursal(
        client_id=client_id,
        sucursal_id=sucursal_id,
        data={"es_activo": False},
        empresa_id=empresa_id,
    )


async def reactivar_sucursal_servicio(
    client_id: UUID,
    sucursal_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> SucursalRead:
    empresa_id = _require_empresa_id(empresa_id)
    row = await get_sucursal_by_id(
        client_id=client_id,
        sucursal_id=sucursal_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Sucursal no encontrada")
    updated = await update_sucursal(
        client_id=client_id,
        sucursal_id=sucursal_id,
        data={"es_activo": True},
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)
