"""Servicio aplicacion svc_orden_servicio."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.svc import (
    list_orden_servicio as _list,
    get_orden_servicio_by_id as _get,
    create_orden_servicio as _create,
    update_orden_servicio as _update,
    assign_orden_servicio_transition as _assign_transition,
    iniciar_orden_servicio_transition as _iniciar_transition,
    completar_orden_servicio_transition as _completar_transition,
    cancelar_orden_servicio_transition as _cancelar_transition,
)
from app.modules.svc.presentation.schemas import (
    OrdenServicioCreate,
    OrdenServicioUpdate,
    OrdenServicioRead,
)
from app.core.exceptions import NotFoundError, ValidationError


def _norm_estado(v: Optional[str]) -> str:
    return (v or "").strip().lower()


async def list_orden_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    cliente_venta_id: Optional[UUID] = None,
    tipo_servicio: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[OrdenServicioRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        estado=estado,
        cliente_venta_id=cliente_venta_id,
        tipo_servicio=tipo_servicio,
        buscar=buscar,
    )
    return [OrdenServicioRead(**dict(r)) for r in rows]


async def get_orden_servicio_by_id(
    client_id: UUID,
    orden_servicio_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> OrdenServicioRead:
    row = await _get(client_id, orden_servicio_id, empresa_id=empresa_id)
    if not row:
        raise NotFoundError("Orden de servicio no encontrada")
    return OrdenServicioRead(**dict(row))


async def create_orden_servicio(
    client_id: UUID, data: OrdenServicioCreate
) -> OrdenServicioRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, dump)
    return OrdenServicioRead(**dict(row))


async def update_orden_servicio(
    client_id: UUID,
    orden_servicio_id: UUID,
    data: OrdenServicioUpdate,
    empresa_id: Optional[UUID] = None,
) -> OrdenServicioRead:
    current = await _get(client_id, orden_servicio_id, empresa_id=empresa_id)
    if not current:
        raise NotFoundError("Orden de servicio no encontrada")
    st = _norm_estado(current.get("estado"))
    if st not in ("solicitada", "asignada"):
        raise ValidationError(
            "Solo se puede editar una orden de servicio en estado solicitada o asignada."
        )
    dump = data.model_dump(exclude_none=True)
    if "estado" in dump and dump["estado"] is not None:
        if _norm_estado(dump["estado"]) != st:
            raise ValidationError(
                "Los cambios de estado deben realizarse mediante los endpoints de transición."
            )
    row = await _update(client_id, orden_servicio_id, dump, empresa_id=empresa_id)
    if not row:
        raise NotFoundError("Orden de servicio no encontrada")
    return OrdenServicioRead(**dict(row))


async def assign_orden_servicio(
    client_id: UUID,
    orden_servicio_id: UUID,
    tecnico_asignado_usuario_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> OrdenServicioRead:
    current = await _get(client_id, orden_servicio_id, empresa_id=empresa_id)
    if not current:
        raise NotFoundError("Orden de servicio no encontrada")
    st = _norm_estado(current.get("estado"))
    if st == "asignada":
        actual = current.get("tecnico_asignado_usuario_id")
        if actual == tecnico_asignado_usuario_id:
            return OrdenServicioRead(**dict(current))
        raise ValidationError("La orden ya está asignada a otro técnico.")
    row = await _assign_transition(
        client_id,
        orden_servicio_id,
        tecnico_asignado_usuario_id,
        empresa_id=empresa_id,
    )
    if row:
        return OrdenServicioRead(**dict(row))
    cur = await _get(client_id, orden_servicio_id, empresa_id=empresa_id)
    if cur and _norm_estado(cur.get("estado")) == "solicitada":
        raise ValidationError(
            "No se pudo asignar la orden; intente nuevamente o verifique el estado."
        )
    raise ValidationError("Solo se puede asignar una orden en estado solicitada.")


async def iniciar_orden_servicio(
    client_id: UUID,
    orden_servicio_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> OrdenServicioRead:
    current = await _get(client_id, orden_servicio_id, empresa_id=empresa_id)
    if not current:
        raise NotFoundError("Orden de servicio no encontrada")
    st = _norm_estado(current.get("estado"))
    if st == "en_proceso":
        return OrdenServicioRead(**dict(current))
    now = datetime.utcnow()
    row = await _iniciar_transition(
        client_id, orden_servicio_id, now, empresa_id=empresa_id
    )
    if row:
        return OrdenServicioRead(**dict(row))
    if st != "asignada":
        raise ValidationError(
            "Solo se puede iniciar una orden en estado asignada."
        )
    raise ValidationError(
        "No se pudo iniciar la orden; intente nuevamente o verifique el estado."
    )


async def completar_orden_servicio(
    client_id: UUID,
    orden_servicio_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> OrdenServicioRead:
    current = await _get(client_id, orden_servicio_id, empresa_id=empresa_id)
    if not current:
        raise NotFoundError("Orden de servicio no encontrada")
    st = _norm_estado(current.get("estado"))
    if st == "completada":
        return OrdenServicioRead(**dict(current))
    now = datetime.utcnow()
    row = await _completar_transition(
        client_id, orden_servicio_id, now, empresa_id=empresa_id
    )
    if row:
        return OrdenServicioRead(**dict(row))
    if st != "en_proceso":
        raise ValidationError(
            "Solo se puede completar una orden en estado en_proceso."
        )
    raise ValidationError(
        "No se pudo completar la orden; intente nuevamente o verifique el estado."
    )


async def cancelar_orden_servicio(
    client_id: UUID,
    orden_servicio_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> OrdenServicioRead:
    current = await _get(client_id, orden_servicio_id, empresa_id=empresa_id)
    if not current:
        raise NotFoundError("Orden de servicio no encontrada")
    st = _norm_estado(current.get("estado"))
    if st == "cancelada":
        return OrdenServicioRead(**dict(current))
    row = await _cancelar_transition(
        client_id, orden_servicio_id, empresa_id=empresa_id
    )
    if row:
        return OrdenServicioRead(**dict(row))
    if st not in ("solicitada", "asignada"):
        raise ValidationError(
            "Solo se puede cancelar una orden en estado solicitada o asignada."
        )
    raise ValidationError(
        "No se pudo cancelar la orden; intente nuevamente o verifique el estado."
    )
