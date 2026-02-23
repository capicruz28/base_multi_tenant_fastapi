"""Servicio aplicacion bdg_presupuesto. Convierte anio <-> año y calcula porcentaje_ejecucion."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.infrastructure.database.queries.bdg import (
    list_presupuesto as _list,
    get_presupuesto_by_id as _get,
    create_presupuesto as _create,
    update_presupuesto as _update,
)
from app.modules.bdg.presentation.schemas import (
    PresupuestoCreate,
    PresupuestoUpdate,
    PresupuestoRead,
)
from app.core.exceptions import NotFoundError


def _row_to_read(row: dict) -> dict:
    r = dict(row)
    if "año" in r:
        r["anio"] = r.pop("año")
    total_pres = r.get("monto_total_presupuestado") or Decimal("0")
    total_ejec = r.get("monto_total_ejecutado") or Decimal("0")
    if total_pres and total_pres > 0:
        r["porcentaje_ejecucion"] = (total_ejec / total_pres) * 100
    else:
        r["porcentaje_ejecucion"] = Decimal("0")
    return r


def _dump_to_db(data: dict) -> dict:
    d = dict(data)
    if "anio" in d:
        d["año"] = d.pop("anio")
    return d


async def list_presupuesto(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    anio: Optional[int] = None,
    tipo_presupuesto: Optional[str] = None,
    estado: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[PresupuestoRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        anio=anio,
        tipo_presupuesto=tipo_presupuesto,
        estado=estado,
        buscar=buscar,
    )
    return [PresupuestoRead(**_row_to_read(r)) for r in rows]


async def get_presupuesto_by_id(client_id: UUID, presupuesto_id: UUID) -> PresupuestoRead:
    row = await _get(client_id, presupuesto_id)
    if not row:
        raise NotFoundError("Presupuesto no encontrado")
    return PresupuestoRead(**_row_to_read(row))


async def create_presupuesto(client_id: UUID, data: PresupuestoCreate) -> PresupuestoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, _dump_to_db(dump))
    return PresupuestoRead(**_row_to_read(row))


async def update_presupuesto(
    client_id: UUID, presupuesto_id: UUID, data: PresupuestoUpdate
) -> PresupuestoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _update(client_id, presupuesto_id, dump)
    if not row:
        raise NotFoundError("Presupuesto no encontrado")
    return PresupuestoRead(**_row_to_read(row))
