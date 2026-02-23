# app/modules/inv/application/services/producto_service.py
"""
Servicio de Producto (INV). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.inv import (
    list_productos,
    get_producto_by_id,
    create_producto,
    update_producto,
)
from app.modules.inv.presentation.schemas import (
    ProductoCreate,
    ProductoUpdate,
    ProductoRead,
)


def _row_to_read(row: dict) -> ProductoRead:
    return ProductoRead(**row)


async def list_productos_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    categoria_id: Optional[UUID] = None,
    tipo_producto: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> List[ProductoRead]:
    rows = await list_productos(
        client_id=client_id,
        empresa_id=empresa_id,
        categoria_id=categoria_id,
        tipo_producto=tipo_producto,
        solo_activos=solo_activos,
        buscar=buscar
    )
    return [_row_to_read(r) for r in rows]


async def get_producto_servicio(
    client_id: UUID,
    producto_id: UUID,
) -> ProductoRead:
    row = await get_producto_by_id(client_id=client_id, producto_id=producto_id)
    if not row:
        raise NotFoundError(detail="Producto no encontrado")
    return _row_to_read(row)


async def create_producto_servicio(
    client_id: UUID,
    data: ProductoCreate,
) -> ProductoRead:
    payload = data.model_dump()
    row = await create_producto(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_producto_servicio(
    client_id: UUID,
    producto_id: UUID,
    data: ProductoUpdate,
) -> ProductoRead:
    row = await get_producto_by_id(client_id=client_id, producto_id=producto_id)
    if not row:
        raise NotFoundError(detail="Producto no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_producto(client_id=client_id, producto_id=producto_id, data=payload)
    return _row_to_read(updated)
