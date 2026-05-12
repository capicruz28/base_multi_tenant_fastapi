"""Servicio aplicación bdg_presupuesto_detalle. Calcula monto_disponible en Read."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.infrastructure.database.queries.bdg import (
    list_presupuesto_detalle as _list,
    get_presupuesto_detalle_by_id as _get,
    create_presupuesto_detalle as _create,
    update_presupuesto_detalle as _update,
    get_presupuesto_by_id as _get_presupuesto,
)
from app.modules.bdg.presentation.schemas import (
    PresupuestoDetalleCreate,
    PresupuestoDetalleUpdate,
    PresupuestoDetalleRead,
)
from app.core.exceptions import NotFoundError, ServiceError


def _estado_norm(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _validar_borrador(row: dict) -> None:
    if _estado_norm(row.get("estado")) != "borrador":
        raise ServiceError(
            status_code=400,
            detail="Solo se pueden modificar detalles de presupuestos en estado borrador.",
            internal_code="BDG_PRESUPUESTO_DETALLE_NOT_BORRADOR",
        )


def _row_to_read(row: dict) -> dict:
    r = dict(row)
    pres = r.get("monto_presupuestado") or Decimal("0")
    ejec = r.get("monto_ejecutado") or Decimal("0")
    r["monto_disponible"] = pres - ejec
    return r


async def list_presupuesto_detalle(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    presupuesto_id: Optional[UUID] = None,
    cuenta_id: Optional[UUID] = None,
    centro_costo_id: Optional[UUID] = None,
    mes: Optional[int] = None,
) -> List[PresupuestoDetalleRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        presupuesto_id=presupuesto_id,
        cuenta_id=cuenta_id,
        centro_costo_id=centro_costo_id,
        mes=mes,
    )
    return [PresupuestoDetalleRead(**_row_to_read(r)) for r in rows]


async def get_presupuesto_detalle_by_id(
    client_id: UUID,
    presupuesto_detalle_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> PresupuestoDetalleRead:
    row = await _get(client_id, presupuesto_detalle_id, empresa_id=empresa_id)
    if not row:
        raise NotFoundError("Detalle de presupuesto no encontrado")
    return PresupuestoDetalleRead(**_row_to_read(row))


async def create_presupuesto_detalle(
    client_id: UUID, data: PresupuestoDetalleCreate
) -> PresupuestoDetalleRead:
    dump = data.model_dump(exclude_none=True)
    presupuesto = await _get_presupuesto(client_id, data.presupuesto_id)
    if not presupuesto:
        raise NotFoundError("Presupuesto no encontrado")
    _validar_borrador(presupuesto)
    row = await _create(client_id, dump)
    if not row:
        raise NotFoundError("Presupuesto no encontrado")
    return PresupuestoDetalleRead(**_row_to_read(row))


async def update_presupuesto_detalle(
    client_id: UUID,
    presupuesto_detalle_id: UUID,
    data: PresupuestoDetalleUpdate,
    empresa_id: Optional[UUID] = None,
) -> PresupuestoDetalleRead:
    current = await _get(client_id, presupuesto_detalle_id, empresa_id=empresa_id)
    if not current:
        raise NotFoundError("Detalle de presupuesto no encontrado")
    presupuesto = await _get_presupuesto(
        client_id,
        current["presupuesto_id"],
        empresa_id=current.get("empresa_id"),
    )
    if not presupuesto:
        raise NotFoundError("Presupuesto no encontrado")
    _validar_borrador(presupuesto)
    dump = data.model_dump(exclude_none=True)
    row = await _update(
        client_id,
        presupuesto_detalle_id,
        dump,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError("Detalle de presupuesto no encontrado")
    return PresupuestoDetalleRead(**_row_to_read(row))
