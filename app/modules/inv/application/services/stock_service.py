# app/modules/inv/application/services/stock_service.py
"""
Servicio de Stock (INV). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.inv import (
    list_stocks,
    get_stock_by_id,
    get_stock_by_producto_almacen,
    create_stock,
    update_stock,
)
from app.modules.inv.presentation.schemas import (
    StockCreate,
    StockUpdate,
    StockRead,
)


def _row_to_read(row: dict) -> StockRead:
    return StockRead(**row)


async def list_stocks_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
) -> List[StockRead]:
    rows = await list_stocks(
        client_id=client_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        almacen_id=almacen_id
    )
    return [_row_to_read(r) for r in rows]


async def get_stock_servicio(
    client_id: UUID,
    stock_id: UUID,
) -> StockRead:
    row = await get_stock_by_id(client_id=client_id, stock_id=stock_id)
    if not row:
        raise NotFoundError(detail="Stock no encontrado")
    return _row_to_read(row)


async def get_stock_by_producto_almacen_servicio(
    client_id: UUID,
    producto_id: UUID,
    almacen_id: UUID,
) -> Optional[StockRead]:
    row = await get_stock_by_producto_almacen(
        client_id=client_id,
        producto_id=producto_id,
        almacen_id=almacen_id
    )
    return _row_to_read(row) if row else None


async def create_stock_servicio(
    client_id: UUID,
    data: StockCreate,
) -> StockRead:
    payload = data.model_dump()
    row = await create_stock(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_stock_servicio(
    client_id: UUID,
    stock_id: UUID,
    data: StockUpdate,
) -> StockRead:
    row = await get_stock_by_id(client_id=client_id, stock_id=stock_id)
    if not row:
        raise NotFoundError(detail="Stock no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_stock(client_id=client_id, stock_id=stock_id, data=payload)
    return _row_to_read(updated)
