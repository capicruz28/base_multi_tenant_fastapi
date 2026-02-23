"""Servicio aplicación tax_libro_electronico. Convierte anio <-> año."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.tax import (
    list_libro_electronico as _list,
    get_libro_electronico_by_id as _get,
    create_libro_electronico as _create,
    update_libro_electronico as _update,
)
from app.modules.tax.presentation.schemas import (
    LibroElectronicoCreate,
    LibroElectronicoUpdate,
    LibroElectronicoRead,
)
from app.core.exceptions import NotFoundError


def _row_to_read(row: dict) -> dict:
    r = dict(row)
    if "año" in r:
        r["anio"] = r.pop("año")
    return r


def _dump_to_db(data: dict) -> dict:
    d = dict(data)
    if "anio" in d:
        d["año"] = d.pop("anio")
    return d


async def list_libro_electronico(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_libro: Optional[str] = None,
    anio: Optional[int] = None,
    mes: Optional[int] = None,
    estado: Optional[str] = None,
) -> List[LibroElectronicoRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_libro=tipo_libro,
        anio=anio,
        mes=mes,
        estado=estado,
    )
    return [LibroElectronicoRead(**_row_to_read(r)) for r in rows]


async def get_libro_electronico_by_id(client_id: UUID, libro_id: UUID) -> LibroElectronicoRead:
    row = await _get(client_id, libro_id)
    if not row:
        raise NotFoundError("Libro electrónico no encontrado")
    return LibroElectronicoRead(**_row_to_read(row))


async def create_libro_electronico(client_id: UUID, data: LibroElectronicoCreate) -> LibroElectronicoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, _dump_to_db(dump))
    return LibroElectronicoRead(**_row_to_read(row))


async def update_libro_electronico(
    client_id: UUID, libro_id: UUID, data: LibroElectronicoUpdate
) -> LibroElectronicoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _update(client_id, libro_id, dump)
    if not row:
        raise NotFoundError("Libro electrónico no encontrado")
    return LibroElectronicoRead(**_row_to_read(row))
