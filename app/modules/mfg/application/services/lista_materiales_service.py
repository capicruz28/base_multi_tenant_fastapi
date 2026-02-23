"""Servicio aplicación mfg_lista_materiales (BOM)."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mfg import (
    list_listas_materiales as _list,
    get_lista_materiales_by_id as _get,
    create_lista_materiales as _create,
    update_lista_materiales as _update,
)
from app.modules.mfg.presentation.schemas import ListaMaterialesCreate, ListaMaterialesUpdate, ListaMaterialesRead
from app.core.exceptions import NotFoundError

async def list_listas_materiales(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    es_bom_activa: Optional[bool] = None,
    estado: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[ListaMaterialesRead]:
    rows = await _list(client_id=client_id, empresa_id=empresa_id, producto_id=producto_id, es_bom_activa=es_bom_activa, estado=estado, buscar=buscar)
    return [ListaMaterialesRead(**r) for r in rows]

async def get_lista_materiales_by_id(client_id: UUID, bom_id: UUID) -> ListaMaterialesRead:
    row = await _get(client_id, bom_id)
    if not row:
        raise NotFoundError(f"Lista de materiales (BOM) {bom_id} no encontrada")
    return ListaMaterialesRead(**row)

async def create_lista_materiales(client_id: UUID, data: ListaMaterialesCreate) -> ListaMaterialesRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return ListaMaterialesRead(**row)

async def update_lista_materiales(client_id: UUID, bom_id: UUID, data: ListaMaterialesUpdate) -> ListaMaterialesRead:
    row = await _update(client_id, bom_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Lista de materiales (BOM) {bom_id} no encontrada")
    return ListaMaterialesRead(**row)
