"""Servicio aplicación mps_pronostico_demanda. Convierte anio <-> año para API/BD."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.infrastructure.database.queries.mps import (
    list_pronostico_demanda as _list,
    get_pronostico_demanda_by_id as _get,
    create_pronostico_demanda as _create,
    update_pronostico_demanda as _update,
)
from app.modules.mps.presentation.schemas import (
    PronosticoDemandaCreate,
    PronosticoDemandaUpdate,
    PronosticoDemandaRead,
)
from app.core.exceptions import NotFoundError


def _row_to_read(row: dict) -> dict:
    r = dict(row)
    r["anio"] = r.pop("año", None)
    if r.get("cantidad_real") is not None and r.get("cantidad_pronosticada") is not None:
        r["desviacion"] = r["cantidad_real"] - r["cantidad_pronosticada"]
    return r


def _dump_to_db(data: dict) -> dict:
    d = dict(data)
    if "anio" in d:
        d["año"] = d.pop("anio")
    return d


async def list_pronostico_demanda(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    anio: Optional[int] = None,
    mes: Optional[int] = None,
) -> List[PronosticoDemandaRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        anio=anio,
        mes=mes,
    )
    return [PronosticoDemandaRead(**_row_to_read(r)) for r in rows]


async def get_pronostico_demanda_by_id(client_id: UUID, pronostico_id: UUID) -> PronosticoDemandaRead:
    row = await _get(client_id, pronostico_id)
    if not row:
        raise NotFoundError(f"Pronóstico demanda {pronostico_id} no encontrado")
    return PronosticoDemandaRead(**_row_to_read(row))


async def create_pronostico_demanda(client_id: UUID, data: PronosticoDemandaCreate) -> PronosticoDemandaRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, _dump_to_db(dump))
    return PronosticoDemandaRead(**_row_to_read(row))


async def update_pronostico_demanda(
    client_id: UUID, pronostico_id: UUID, data: PronosticoDemandaUpdate
) -> PronosticoDemandaRead:
    dump = data.model_dump(exclude_none=True)
    row = await _update(client_id, pronostico_id, _dump_to_db(dump))
    if not row:
        raise NotFoundError(f"Pronóstico demanda {pronostico_id} no encontrado")
    return PronosticoDemandaRead(**_row_to_read(row))
