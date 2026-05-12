"""Servicio aplicación mfg_orden_produccion."""
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.mfg import (
    list_ordenes_produccion as _list,
    get_orden_produccion_by_id as _get,
    create_orden_produccion as _create,
    update_orden_produccion as _update,
)
from app.modules.mfg.presentation.schemas import OrdenProduccionCreate, OrdenProduccionUpdate, OrdenProduccionRead
from app.core.exceptions import NotFoundError, ServiceError

_ESTADO_OP_BORRADOR = "borrador"
_ESTADO_OP_LIBERADA = "liberada"
_ESTADO_OP_EN_PROCESO = "en_proceso"
_ESTADO_OP_COMPLETADA = "completada"
_ESTADO_OP_CERRADA = "cerrada"
_ESTADO_OP_ANULADA = "anulada"
_ESTADO_OP_PAUSADA = "pausada"

_OP_EDITABLE_STATES = {_ESTADO_OP_BORRADOR}


def _assert_op_editable(estado: Optional[str]) -> None:
    if (estado or "").strip().lower() not in _OP_EDITABLE_STATES:
        raise ServiceError(
            status_code=409,
            detail=f"No se permite editar la orden de producción en estado '{estado}'. Solo se permite en: {sorted(_OP_EDITABLE_STATES)}",
            internal_code="MFG_OP_NOT_EDITABLE",
        )


def _assert_transition(current: str, allowed_from: set[str], action: str) -> None:
    if current not in allowed_from:
        raise ServiceError(
            status_code=409,
            detail=f"No se puede '{action}' una orden de producción desde estado '{current}'. Estados permitidos: {sorted(allowed_from)}",
            internal_code="MFG_OP_INVALID_TRANSITION",
        )

async def list_ordenes_produccion(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[OrdenProduccionRead]:
    if empresa_id is not None:
        await get_empresa_servicio(client_id=client_id, empresa_id=empresa_id)
    rows = await _list(client_id=client_id, empresa_id=empresa_id, producto_id=producto_id, estado=estado, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    return [OrdenProduccionRead(**r) for r in rows]

async def get_orden_produccion_by_id(client_id: UUID, orden_produccion_id: UUID) -> OrdenProduccionRead:
    row = await _get(client_id, orden_produccion_id)
    if not row:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=row["empresa_id"])
    return OrdenProduccionRead(**row)

async def create_orden_produccion(client_id: UUID, data: OrdenProduccionCreate) -> OrdenProduccionRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return OrdenProduccionRead(**row)

async def update_orden_produccion(client_id: UUID, orden_produccion_id: UUID, data: OrdenProduccionUpdate) -> OrdenProduccionRead:
    current = await _get(client_id, orden_produccion_id)
    if not current:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=current["empresa_id"])
    _assert_op_editable(current.get("estado"))

    payload = data.model_dump(exclude_none=True)
    payload.pop("estado", None)  # estado se cambia solo por transiciones explícitas

    row = await _update(client_id, orden_produccion_id, payload)
    if not row:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    return OrdenProduccionRead(**row)


async def liberar_orden_produccion(client_id: UUID, orden_produccion_id: UUID) -> OrdenProduccionRead:
    current = await _get(client_id, orden_produccion_id)
    if not current:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=current["empresa_id"])
    estado_actual = (current.get("estado") or "").strip().lower()
    _assert_transition(estado_actual, {_ESTADO_OP_BORRADOR}, "liberar")

    row = await _update(client_id, orden_produccion_id, {"estado": _ESTADO_OP_LIBERADA})
    if not row:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    return OrdenProduccionRead(**row)


async def iniciar_orden_produccion(client_id: UUID, orden_produccion_id: UUID) -> OrdenProduccionRead:
    current = await _get(client_id, orden_produccion_id)
    if not current:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=current["empresa_id"])
    estado_actual = (current.get("estado") or "").strip().lower()
    _assert_transition(estado_actual, {_ESTADO_OP_LIBERADA, _ESTADO_OP_PAUSADA}, "iniciar")

    row = await _update(client_id, orden_produccion_id, {"estado": _ESTADO_OP_EN_PROCESO})
    if not row:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    return OrdenProduccionRead(**row)


async def finalizar_orden_produccion(client_id: UUID, orden_produccion_id: UUID) -> OrdenProduccionRead:
    current = await _get(client_id, orden_produccion_id)
    if not current:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=current["empresa_id"])
    estado_actual = (current.get("estado") or "").strip().lower()
    _assert_transition(estado_actual, {_ESTADO_OP_EN_PROCESO, _ESTADO_OP_PAUSADA}, "finalizar")

    row = await _update(client_id, orden_produccion_id, {"estado": _ESTADO_OP_COMPLETADA})
    if not row:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    return OrdenProduccionRead(**row)


async def cerrar_orden_produccion(client_id: UUID, orden_produccion_id: UUID) -> OrdenProduccionRead:
    current = await _get(client_id, orden_produccion_id)
    if not current:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=current["empresa_id"])
    estado_actual = (current.get("estado") or "").strip().lower()
    _assert_transition(estado_actual, {_ESTADO_OP_COMPLETADA}, "cerrar")

    row = await _update(client_id, orden_produccion_id, {"estado": _ESTADO_OP_CERRADA})
    if not row:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    return OrdenProduccionRead(**row)


async def anular_orden_produccion(client_id: UUID, orden_produccion_id: UUID) -> OrdenProduccionRead:
    current = await _get(client_id, orden_produccion_id)
    if not current:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=current["empresa_id"])
    estado_actual = (current.get("estado") or "").strip().lower()
    _assert_transition(estado_actual, {_ESTADO_OP_BORRADOR, _ESTADO_OP_LIBERADA}, "anular")

    row = await _update(client_id, orden_produccion_id, {"estado": _ESTADO_OP_ANULADA})
    if not row:
        raise NotFoundError(f"Orden de producción {orden_produccion_id} no encontrada")
    return OrdenProduccionRead(**row)
