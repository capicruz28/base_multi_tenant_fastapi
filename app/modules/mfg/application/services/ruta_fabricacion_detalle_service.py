"""Servicio aplicación mfg_ruta_fabricacion_detalle."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mfg import (
    list_ruta_fabricacion_detalles as _list,
    get_ruta_fabricacion_detalle_by_id as _get,
    get_ruta_fabricacion_by_id as _get_ruta,
    create_ruta_fabricacion_detalle as _create,
    update_ruta_fabricacion_detalle as _update,
)
from app.modules.mfg.presentation.schemas import RutaFabricacionDetalleCreate, RutaFabricacionDetalleUpdate, RutaFabricacionDetalleRead
from app.core.exceptions import NotFoundError, ServiceError

_ESTADO_RUTA_EDITABLE = "borrador"


def _assert_ruta_editable(estado: Optional[str]) -> None:
    if (estado or "").strip().lower() != _ESTADO_RUTA_EDITABLE:
        raise ServiceError(
            status_code=409,
            detail=f"No se permite modificar el detalle de ruta cuando la cabecera no está en '{_ESTADO_RUTA_EDITABLE}'. Estado actual: '{estado}'.",
            internal_code="MFG_RUTA_DET_NOT_EDITABLE",
        )

async def list_ruta_fabricacion_detalles(client_id: UUID, ruta_id: Optional[UUID] = None) -> List[RutaFabricacionDetalleRead]:
    rows = await _list(client_id=client_id, ruta_id=ruta_id)
    return [RutaFabricacionDetalleRead(**r) for r in rows]

async def get_ruta_fabricacion_detalle_by_id(client_id: UUID, ruta_detalle_id: UUID) -> RutaFabricacionDetalleRead:
    row = await _get(client_id, ruta_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle ruta {ruta_detalle_id} no encontrado")
    return RutaFabricacionDetalleRead(**row)

async def create_ruta_fabricacion_detalle(client_id: UUID, data: RutaFabricacionDetalleCreate) -> RutaFabricacionDetalleRead:
    ruta = await _get_ruta(client_id=client_id, ruta_id=data.ruta_id)
    if not ruta:
        raise NotFoundError(f"Ruta de fabricación {data.ruta_id} no encontrada")
    _assert_ruta_editable(ruta.get("estado"))
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return RutaFabricacionDetalleRead(**row)

async def update_ruta_fabricacion_detalle(client_id: UUID, ruta_detalle_id: UUID, data: RutaFabricacionDetalleUpdate) -> RutaFabricacionDetalleRead:
    current = await _get(client_id, ruta_detalle_id)
    if not current:
        raise NotFoundError(f"Detalle ruta {ruta_detalle_id} no encontrado")
    ruta = await _get_ruta(client_id=client_id, ruta_id=current["ruta_id"])
    if not ruta:
        raise NotFoundError(f"Ruta de fabricación {current['ruta_id']} no encontrada")
    _assert_ruta_editable(ruta.get("estado"))

    row = await _update(client_id, ruta_detalle_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Detalle ruta {ruta_detalle_id} no encontrado")
    return RutaFabricacionDetalleRead(**row)
