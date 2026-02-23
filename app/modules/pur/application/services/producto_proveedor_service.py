# app/modules/pur/application/services/producto_proveedor_service.py
"""
Servicio de Producto por Proveedor (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.pur import (
    list_productos_proveedor,
    get_producto_proveedor_by_id,
    create_producto_proveedor,
    update_producto_proveedor,
)
from app.modules.pur.presentation.schemas import (
    ProductoProveedorCreate,
    ProductoProveedorUpdate,
    ProductoProveedorRead,
)


def _row_to_read(row: dict) -> ProductoProveedorRead:
    return ProductoProveedorRead(**row)


async def list_productos_proveedor_servicio(
    client_id: UUID,
    proveedor_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    solo_activos: bool = True,
) -> List[ProductoProveedorRead]:
    rows = await list_productos_proveedor(
        client_id=client_id,
        proveedor_id=proveedor_id,
        producto_id=producto_id,
        solo_activos=solo_activos
    )
    return [_row_to_read(r) for r in rows]


async def get_producto_proveedor_servicio(
    client_id: UUID,
    producto_proveedor_id: UUID,
) -> ProductoProveedorRead:
    row = await get_producto_proveedor_by_id(client_id=client_id, producto_proveedor_id=producto_proveedor_id)
    if not row:
        raise NotFoundError(detail="Producto por proveedor no encontrado")
    return _row_to_read(row)


async def create_producto_proveedor_servicio(
    client_id: UUID,
    data: ProductoProveedorCreate,
) -> ProductoProveedorRead:
    payload = data.model_dump()
    row = await create_producto_proveedor(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_producto_proveedor_servicio(
    client_id: UUID,
    producto_proveedor_id: UUID,
    data: ProductoProveedorUpdate,
) -> ProductoProveedorRead:
    row = await get_producto_proveedor_by_id(client_id=client_id, producto_proveedor_id=producto_proveedor_id)
    if not row:
        raise NotFoundError(detail="Producto por proveedor no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_producto_proveedor(client_id=client_id, producto_proveedor_id=producto_proveedor_id, data=payload)
    return _row_to_read(updated)
