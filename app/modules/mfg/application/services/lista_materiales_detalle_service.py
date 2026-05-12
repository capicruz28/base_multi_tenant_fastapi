"""Servicio aplicación mfg_lista_materiales_detalle."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mfg import (
    list_lista_materiales_detalles as _list,
    get_lista_materiales_detalle_by_id as _get,
    get_lista_materiales_by_id as _get_bom,
    create_lista_materiales_detalle as _create,
    update_lista_materiales_detalle as _update,
)
from app.modules.mfg.presentation.schemas import ListaMaterialesDetalleCreate, ListaMaterialesDetalleUpdate, ListaMaterialesDetalleRead
from app.core.exceptions import NotFoundError, ServiceError

_ESTADO_BOM_EDITABLE = "borrador"


def _assert_bom_editable(estado: Optional[str]) -> None:
    if (estado or "").strip().lower() != _ESTADO_BOM_EDITABLE:
        raise ServiceError(
            status_code=409,
            detail=f"No se permite modificar el detalle de BOM cuando la cabecera no está en '{_ESTADO_BOM_EDITABLE}'. Estado actual: '{estado}'.",
            internal_code="MFG_BOM_DET_NOT_EDITABLE",
        )

async def list_lista_materiales_detalles(client_id: UUID, bom_id: Optional[UUID] = None) -> List[ListaMaterialesDetalleRead]:
    rows = await _list(client_id=client_id, bom_id=bom_id)
    return [ListaMaterialesDetalleRead(**r) for r in rows]

async def get_lista_materiales_detalle_by_id(client_id: UUID, bom_detalle_id: UUID) -> ListaMaterialesDetalleRead:
    row = await _get(client_id, bom_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle BOM {bom_detalle_id} no encontrado")
    return ListaMaterialesDetalleRead(**row)

async def create_lista_materiales_detalle(client_id: UUID, data: ListaMaterialesDetalleCreate) -> ListaMaterialesDetalleRead:
    bom = await _get_bom(client_id=client_id, bom_id=data.bom_id)
    if not bom:
        raise NotFoundError(f"Lista de materiales (BOM) {data.bom_id} no encontrada")
    _assert_bom_editable(bom.get("estado"))
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return ListaMaterialesDetalleRead(**row)

async def update_lista_materiales_detalle(client_id: UUID, bom_detalle_id: UUID, data: ListaMaterialesDetalleUpdate) -> ListaMaterialesDetalleRead:
    current = await _get(client_id, bom_detalle_id)
    if not current:
        raise NotFoundError(f"Detalle BOM {bom_detalle_id} no encontrado")
    bom = await _get_bom(client_id=client_id, bom_id=current["bom_id"])
    if not bom:
        raise NotFoundError(f"Lista de materiales (BOM) {current['bom_id']} no encontrada")
    _assert_bom_editable(bom.get("estado"))

    row = await _update(client_id, bom_detalle_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Detalle BOM {bom_detalle_id} no encontrado")
    return ListaMaterialesDetalleRead(**row)
