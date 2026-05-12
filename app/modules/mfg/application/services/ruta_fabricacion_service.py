"""Servicio aplicación mfg_ruta_fabricacion."""
from typing import List, Optional
from uuid import UUID
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.mfg import (
    list_rutas_fabricacion as _list,
    get_ruta_fabricacion_by_id as _get,
    create_ruta_fabricacion as _create,
    update_ruta_fabricacion as _update,
)
from app.modules.mfg.presentation.schemas import RutaFabricacionCreate, RutaFabricacionUpdate, RutaFabricacionRead
from app.core.exceptions import NotFoundError, ServiceError

_ESTADO_RUTA_BORRADOR = "borrador"
_ESTADO_RUTA_APROBADA = "aprobada"
_ESTADO_RUTA_OBSOLETA = "obsoleta"

_RUTA_EDITABLE_STATES = {_ESTADO_RUTA_BORRADOR}


def _assert_ruta_editable(estado: Optional[str]) -> None:
    if (estado or "").strip().lower() not in _RUTA_EDITABLE_STATES:
        raise ServiceError(
            status_code=409,
            detail=f"No se permite editar la ruta en estado '{estado}'. Solo se permite en: {sorted(_RUTA_EDITABLE_STATES)}",
            internal_code="MFG_RUTA_NOT_EDITABLE",
        )


def _assert_transition(current: str, allowed_from: set[str], action: str) -> None:
    if current not in allowed_from:
        raise ServiceError(
            status_code=409,
            detail=f"No se puede '{action}' una ruta desde estado '{current}'. Estados permitidos: {sorted(allowed_from)}",
            internal_code="MFG_RUTA_INVALID_TRANSITION",
        )

async def list_rutas_fabricacion(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    es_ruta_activa: Optional[bool] = None,
    estado: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[RutaFabricacionRead]:
    if empresa_id is not None:
        await get_empresa_servicio(client_id=client_id, empresa_id=empresa_id)
    rows = await _list(client_id=client_id, empresa_id=empresa_id, producto_id=producto_id, es_ruta_activa=es_ruta_activa, estado=estado, buscar=buscar)
    return [RutaFabricacionRead(**r) for r in rows]

async def get_ruta_fabricacion_by_id(client_id: UUID, ruta_id: UUID) -> RutaFabricacionRead:
    row = await _get(client_id, ruta_id)
    if not row:
        raise NotFoundError(f"Ruta de fabricación {ruta_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=row["empresa_id"])
    return RutaFabricacionRead(**row)

async def create_ruta_fabricacion(client_id: UUID, data: RutaFabricacionCreate) -> RutaFabricacionRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return RutaFabricacionRead(**row)

async def update_ruta_fabricacion(client_id: UUID, ruta_id: UUID, data: RutaFabricacionUpdate) -> RutaFabricacionRead:
    current = await _get(client_id, ruta_id)
    if not current:
        raise NotFoundError(f"Ruta de fabricación {ruta_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=current["empresa_id"])
    _assert_ruta_editable(current.get("estado"))

    payload = data.model_dump(exclude_none=True)
    payload.pop("estado", None)  # estado se cambia solo por transiciones explícitas

    row = await _update(client_id, ruta_id, payload)
    if not row:
        raise NotFoundError(f"Ruta de fabricación {ruta_id} no encontrada")
    return RutaFabricacionRead(**row)


async def aprobar_ruta_fabricacion(client_id: UUID, ruta_id: UUID) -> RutaFabricacionRead:
    current = await _get(client_id, ruta_id)
    if not current:
        raise NotFoundError(f"Ruta de fabricación {ruta_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=current["empresa_id"])
    estado_actual = (current.get("estado") or "").strip().lower()
    _assert_transition(estado_actual, {_ESTADO_RUTA_BORRADOR}, "aprobar")

    row = await _update(client_id, ruta_id, {"estado": _ESTADO_RUTA_APROBADA})
    if not row:
        raise NotFoundError(f"Ruta de fabricación {ruta_id} no encontrada")
    return RutaFabricacionRead(**row)


async def anular_ruta_fabricacion(client_id: UUID, ruta_id: UUID) -> RutaFabricacionRead:
    current = await _get(client_id, ruta_id)
    if not current:
        raise NotFoundError(f"Ruta de fabricación {ruta_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=current["empresa_id"])
    estado_actual = (current.get("estado") or "").strip().lower()
    _assert_transition(estado_actual, {_ESTADO_RUTA_BORRADOR, _ESTADO_RUTA_APROBADA}, "anular")

    row = await _update(client_id, ruta_id, {"estado": _ESTADO_RUTA_OBSOLETA, "es_ruta_activa": False})
    if not row:
        raise NotFoundError(f"Ruta de fabricación {ruta_id} no encontrada")
    return RutaFabricacionRead(**row)
