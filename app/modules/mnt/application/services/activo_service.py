"""Servicio aplicación mnt_activo. Convierte anio_fabricacion <-> año_fabricacion para API/BD."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mnt import (
    list_activo as _list,
    get_activo_by_id as _get,
    create_activo as _create,
    update_activo as _update,
)
from app.modules.mnt.presentation.schemas import ActivoCreate, ActivoUpdate, ActivoRead
from app.core.exceptions import NotFoundError


def _row_to_read(row: dict) -> dict:
    r = dict(row)
    if "año_fabricacion" in r:
        r["anio_fabricacion"] = r.pop("año_fabricacion", None)
    return r


def _dump_to_db(data: dict) -> dict:
    d = dict(data)
    if "anio_fabricacion" in d:
        d["año_fabricacion"] = d.pop("anio_fabricacion")
    return d


async def list_activo(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_activo: Optional[str] = None,
    estado_activo: Optional[str] = None,
    criticidad: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[ActivoRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_activo=tipo_activo,
        estado_activo=estado_activo,
        criticidad=criticidad,
        es_activo=es_activo,
        buscar=buscar,
    )
    return [ActivoRead(**_row_to_read(r)) for r in rows]


async def get_activo_by_id(client_id: UUID, activo_id: UUID) -> ActivoRead:
    row = await _get(client_id, activo_id)
    if not row:
        raise NotFoundError(f"Activo {activo_id} no encontrado")
    return ActivoRead(**_row_to_read(row))


async def create_activo(client_id: UUID, data: ActivoCreate) -> ActivoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, _dump_to_db(dump))
    return ActivoRead(**_row_to_read(row))


async def update_activo(client_id: UUID, activo_id: UUID, data: ActivoUpdate) -> ActivoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _update(client_id, activo_id, _dump_to_db(dump))
    if not row:
        raise NotFoundError(f"Activo {activo_id} no encontrado")
    return ActivoRead(**_row_to_read(row))
