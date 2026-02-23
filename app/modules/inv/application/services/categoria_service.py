# app/modules/inv/application/services/categoria_service.py
"""
Servicio de Categoría de Producto (INV). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.inv import (
    list_categorias,
    get_categoria_by_id,
    create_categoria,
    update_categoria,
)
from app.modules.inv.presentation.schemas import (
    CategoriaCreate,
    CategoriaUpdate,
    CategoriaRead,
)


def _row_to_read(row: dict) -> CategoriaRead:
    return CategoriaRead(**row)


async def list_categorias_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
) -> List[CategoriaRead]:
    rows = await list_categorias(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos
    )
    return [_row_to_read(r) for r in rows]


async def get_categoria_servicio(
    client_id: UUID,
    categoria_id: UUID,
) -> CategoriaRead:
    row = await get_categoria_by_id(client_id=client_id, categoria_id=categoria_id)
    if not row:
        raise NotFoundError(detail="Categoría no encontrada")
    return _row_to_read(row)


async def create_categoria_servicio(
    client_id: UUID,
    data: CategoriaCreate,
) -> CategoriaRead:
    payload = data.model_dump()
    row = await create_categoria(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_categoria_servicio(
    client_id: UUID,
    categoria_id: UUID,
    data: CategoriaUpdate,
) -> CategoriaRead:
    row = await get_categoria_by_id(client_id=client_id, categoria_id=categoria_id)
    if not row:
        raise NotFoundError(detail="Categoría no encontrada")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_categoria(client_id=client_id, categoria_id=categoria_id, data=payload)
    return _row_to_read(updated)
