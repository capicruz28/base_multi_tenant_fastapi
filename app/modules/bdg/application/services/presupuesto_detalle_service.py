"""Servicio aplicación bdg_presupuesto_detalle. Calcula monto_disponible en Read."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.infrastructure.database.queries.bdg import (
    list_presupuesto_detalle as _list,
    get_presupuesto_detalle_by_id as _get,
    create_presupuesto_detalle as _create,
    update_presupuesto_detalle as _update,
)
from app.modules.bdg.presentation.schemas import (
    PresupuestoDetalleCreate,
    PresupuestoDetalleUpdate,
    PresupuestoDetalleRead,
)
from app.core.exceptions import NotFoundError


def _row_to_read(row: dict) -> dict:
    r = dict(row)
    pres = r.get("monto_presupuestado") or Decimal("0")
    ejec = r.get("monto_ejecutado") or Decimal("0")
    r["monto_disponible"] = pres - ejec
    return r


async def list_presupuesto_detalle(
    client_id: UUID,
    presupuesto_id: Optional[UUID] = None,
    cuenta_id: Optional[UUID] = None,
    centro_costo_id: Optional[UUID] = None,
    mes: Optional[int] = None,
) -> List[PresupuestoDetalleRead]:
    rows = await _list(
        client_id=client_id,
        presupuesto_id=presupuesto_id,
        cuenta_id=cuenta_id,
        centro_costo_id=centro_costo_id,
        mes=mes,
    )
    return [PresupuestoDetalleRead(**_row_to_read(r)) for r in rows]


async def get_presupuesto_detalle_by_id(
    client_id: UUID, presupuesto_detalle_id: UUID
) -> PresupuestoDetalleRead:
    row = await _get(client_id, presupuesto_detalle_id)
    if not row:
        raise NotFoundError("Detalle de presupuesto no encontrado")
    return PresupuestoDetalleRead(**_row_to_read(row))


async def create_presupuesto_detalle(
    client_id: UUID, data: PresupuestoDetalleCreate
) -> PresupuestoDetalleRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, dump)
    return PresupuestoDetalleRead(**_row_to_read(row))


async def update_presupuesto_detalle(
    client_id: UUID, presupuesto_detalle_id: UUID, data: PresupuestoDetalleUpdate
) -> PresupuestoDetalleRead:
    dump = data.model_dump(exclude_none=True)
    row = await _update(client_id, presupuesto_detalle_id, dump)
    if not row:
        raise NotFoundError("Detalle de presupuesto no encontrado")
    return PresupuestoDetalleRead(**_row_to_read(row))
