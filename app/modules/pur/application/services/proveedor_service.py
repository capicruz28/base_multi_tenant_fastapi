# app/modules/pur/application/services/proveedor_service.py
"""
Servicio de Proveedor (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.pur import (
    list_proveedores,
    get_proveedor_by_id,
    create_proveedor,
    update_proveedor,
)
from app.modules.pur.presentation.schemas import (
    ProveedorCreate,
    ProveedorUpdate,
    ProveedorRead,
)


def _row_to_read(row: dict) -> ProveedorRead:
    return ProveedorRead(**row)


async def list_proveedores_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> List[ProveedorRead]:
    rows = await list_proveedores(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
        buscar=buscar
    )
    return [_row_to_read(r) for r in rows]


async def get_proveedor_servicio(
    client_id: UUID,
    proveedor_id: UUID,
) -> ProveedorRead:
    row = await get_proveedor_by_id(client_id=client_id, proveedor_id=proveedor_id)
    if not row:
        raise NotFoundError(detail="Proveedor no encontrado")
    return _row_to_read(row)


async def create_proveedor_servicio(
    client_id: UUID,
    data: ProveedorCreate,
) -> ProveedorRead:
    payload = data.model_dump()
    row = await create_proveedor(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_proveedor_servicio(
    client_id: UUID,
    proveedor_id: UUID,
    data: ProveedorUpdate,
) -> ProveedorRead:
    row = await get_proveedor_by_id(client_id=client_id, proveedor_id=proveedor_id)
    if not row:
        raise NotFoundError(detail="Proveedor no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_proveedor(client_id=client_id, proveedor_id=proveedor_id, data=payload)
    return _row_to_read(updated)
