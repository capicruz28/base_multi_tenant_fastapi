"""Servicio aplicación mnt_orden_trabajo. Calcula duracion_horas y costo_total si aplica."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from app.infrastructure.database.queries.mnt import (
    list_orden_trabajo as _list,
    get_orden_trabajo_by_id as _get,
    create_orden_trabajo as _create,
    update_orden_trabajo as _update,
)
from app.modules.mnt.presentation.schemas import OrdenTrabajoCreate, OrdenTrabajoUpdate, OrdenTrabajoRead
from app.core.exceptions import NotFoundError


def _enrich_ot(row: dict) -> dict:
    r = dict(row)
    fi = r.get("fecha_inicio_real")
    ff = r.get("fecha_fin_real")
    if fi and ff:
        if isinstance(fi, datetime) and isinstance(ff, datetime):
            delta = ff - fi
            r["duracion_horas"] = Decimal(str(round(delta.total_seconds() / 3600, 2)))
        else:
            r["duracion_horas"] = None
    else:
        r["duracion_horas"] = None
    co = r.get("costo_mano_obra") or Decimal("0")
    cr = r.get("costo_repuestos") or Decimal("0")
    cs = r.get("costo_servicios_terceros") or Decimal("0")
    r["costo_total"] = co + cr + cs
    return r


async def list_orden_trabajo(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    activo_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    tipo_mantenimiento: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[OrdenTrabajoRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        activo_id=activo_id,
        estado=estado,
        tipo_mantenimiento=tipo_mantenimiento,
        buscar=buscar,
    )
    return [OrdenTrabajoRead(**_enrich_ot(r)) for r in rows]


async def get_orden_trabajo_by_id(client_id: UUID, orden_trabajo_id: UUID) -> OrdenTrabajoRead:
    row = await _get(client_id, orden_trabajo_id)
    if not row:
        raise NotFoundError(f"Orden de trabajo {orden_trabajo_id} no encontrada")
    return OrdenTrabajoRead(**_enrich_ot(row))


async def create_orden_trabajo(client_id: UUID, data: OrdenTrabajoCreate) -> OrdenTrabajoRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return OrdenTrabajoRead(**_enrich_ot(row))


async def update_orden_trabajo(
    client_id: UUID, orden_trabajo_id: UUID, data: OrdenTrabajoUpdate
) -> OrdenTrabajoRead:
    row = await _update(client_id, orden_trabajo_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Orden de trabajo {orden_trabajo_id} no encontrada")
    return OrdenTrabajoRead(**_enrich_ot(row))
