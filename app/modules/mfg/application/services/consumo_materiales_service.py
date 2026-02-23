"""Servicio aplicación mfg_consumo_materiales."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mfg import (
    list_consumo_materiales as _list,
    get_consumo_materiales_by_id as _get,
    create_consumo_materiales as _create,
    update_consumo_materiales as _update,
)
from app.modules.mfg.presentation.schemas import ConsumoMaterialesCreate, ConsumoMaterialesUpdate, ConsumoMaterialesRead
from app.core.exceptions import NotFoundError

async def list_consumo_materiales(
    client_id: UUID,
    orden_produccion_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[ConsumoMaterialesRead]:
    rows = await _list(client_id=client_id, orden_produccion_id=orden_produccion_id, producto_id=producto_id)
    return [ConsumoMaterialesRead(**r) for r in rows]

async def get_consumo_materiales_by_id(client_id: UUID, consumo_id: UUID) -> ConsumoMaterialesRead:
    row = await _get(client_id, consumo_id)
    if not row:
        raise NotFoundError(f"Consumo materiales {consumo_id} no encontrado")
    return ConsumoMaterialesRead(**row)

async def create_consumo_materiales(client_id: UUID, data: ConsumoMaterialesCreate) -> ConsumoMaterialesRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return ConsumoMaterialesRead(**row)

async def update_consumo_materiales(client_id: UUID, consumo_id: UUID, data: ConsumoMaterialesUpdate) -> ConsumoMaterialesRead:
    row = await _update(client_id, consumo_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Consumo materiales {consumo_id} no encontrado")
    return ConsumoMaterialesRead(**row)
