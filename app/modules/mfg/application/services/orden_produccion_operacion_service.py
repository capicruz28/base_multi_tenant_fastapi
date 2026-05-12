"""Servicio aplicación mfg_orden_produccion_operacion."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mfg import (
    list_orden_produccion_operaciones as _list,
    get_orden_produccion_operacion_by_id as _get,
    get_orden_produccion_by_id as _get_op,
    create_orden_produccion_operacion as _create,
    update_orden_produccion_operacion as _update,
)
from app.modules.mfg.presentation.schemas import OrdenProduccionOperacionCreate, OrdenProduccionOperacionUpdate, OrdenProduccionOperacionRead
from app.core.exceptions import NotFoundError, ServiceError

_ESTADO_OP_EDITABLE = "borrador"


def _assert_op_editable(estado: Optional[str]) -> None:
    if (estado or "").strip().lower() != _ESTADO_OP_EDITABLE:
        raise ServiceError(
            status_code=409,
            detail=f"No se permite modificar operaciones de OP cuando la cabecera no está en '{_ESTADO_OP_EDITABLE}'. Estado actual: '{estado}'.",
            internal_code="MFG_OP_OPER_NOT_EDITABLE",
        )

async def list_orden_produccion_operaciones(
    client_id: UUID,
    orden_produccion_id: Optional[UUID] = None,
    centro_trabajo_id: Optional[UUID] = None,
    estado: Optional[str] = None,
) -> List[OrdenProduccionOperacionRead]:
    rows = await _list(client_id=client_id, orden_produccion_id=orden_produccion_id, centro_trabajo_id=centro_trabajo_id, estado=estado)
    return [OrdenProduccionOperacionRead(**r) for r in rows]

async def get_orden_produccion_operacion_by_id(client_id: UUID, op_operacion_id: UUID) -> OrdenProduccionOperacionRead:
    row = await _get(client_id, op_operacion_id)
    if not row:
        raise NotFoundError(f"Operación de OP {op_operacion_id} no encontrada")
    return OrdenProduccionOperacionRead(**row)

async def create_orden_produccion_operacion(client_id: UUID, data: OrdenProduccionOperacionCreate) -> OrdenProduccionOperacionRead:
    op = await _get_op(client_id=client_id, orden_produccion_id=data.orden_produccion_id)
    if not op:
        raise NotFoundError(f"Orden de producción {data.orden_produccion_id} no encontrada")
    _assert_op_editable(op.get("estado"))
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return OrdenProduccionOperacionRead(**row)

async def update_orden_produccion_operacion(client_id: UUID, op_operacion_id: UUID, data: OrdenProduccionOperacionUpdate) -> OrdenProduccionOperacionRead:
    current = await _get(client_id, op_operacion_id)
    if not current:
        raise NotFoundError(f"Operación de OP {op_operacion_id} no encontrada")
    op = await _get_op(client_id=client_id, orden_produccion_id=current["orden_produccion_id"])
    if not op:
        raise NotFoundError(f"Orden de producción {current['orden_produccion_id']} no encontrada")
    _assert_op_editable(op.get("estado"))

    row = await _update(client_id, op_operacion_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Operación de OP {op_operacion_id} no encontrada")
    return OrdenProduccionOperacionRead(**row)
