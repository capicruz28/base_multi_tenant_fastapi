"""Servicio aplicación mfg_consumo_materiales."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mfg import (
    list_consumo_materiales as _list,
    get_consumo_materiales_by_id as _get,
    get_orden_produccion_by_id as _get_op,
    create_consumo_materiales as _create,
    update_consumo_materiales as _update,
)
from app.modules.mfg.presentation.schemas import ConsumoMaterialesCreate, ConsumoMaterialesUpdate, ConsumoMaterialesRead
from app.core.exceptions import NotFoundError, ServiceError

_ESTADO_OP_EDITABLE = "borrador"


def _assert_op_editable(estado: Optional[str]) -> None:
    if (estado or "").strip().lower() != _ESTADO_OP_EDITABLE:
        raise ServiceError(
            status_code=409,
            detail=f"No se permite modificar consumo de materiales cuando la OP no está en '{_ESTADO_OP_EDITABLE}'. Estado actual: '{estado}'.",
            internal_code="MFG_CONSUMO_NOT_EDITABLE",
        )

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
    op = await _get_op(client_id=client_id, orden_produccion_id=data.orden_produccion_id)
    if not op:
        raise NotFoundError(f"Orden de producción {data.orden_produccion_id} no encontrada")
    _assert_op_editable(op.get("estado"))
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return ConsumoMaterialesRead(**row)

async def update_consumo_materiales(client_id: UUID, consumo_id: UUID, data: ConsumoMaterialesUpdate) -> ConsumoMaterialesRead:
    current = await _get(client_id, consumo_id)
    if not current:
        raise NotFoundError(f"Consumo materiales {consumo_id} no encontrado")
    op = await _get_op(client_id=client_id, orden_produccion_id=current["orden_produccion_id"])
    if not op:
        raise NotFoundError(f"Orden de producción {current['orden_produccion_id']} no encontrada")
    _assert_op_editable(op.get("estado"))

    row = await _update(client_id, consumo_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Consumo materiales {consumo_id} no encontrado")
    return ConsumoMaterialesRead(**row)
