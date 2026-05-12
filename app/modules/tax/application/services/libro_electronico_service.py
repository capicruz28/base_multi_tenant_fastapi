"""Servicio aplicación tax_libro_electronico. Convierte anio <-> año; control de estados."""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.infrastructure.database.queries.tax import (
    list_libro_electronico as _list,
    get_libro_electronico_by_id as _get,
    create_libro_electronico as _create,
    update_libro_electronico as _update,
    transition_libro_electronico_estado as _transition,
)
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.modules.tax.application.libro_estados import (
    ANULADO,
    BORRADOR,
    ENVIADO,
    ESTADOS_ANULABLES,
    GENERADO,
)
from app.modules.tax.presentation.schemas import (
    LibroElectronicoCreate,
    LibroElectronicoRegistrarEnvio,
    LibroElectronicoUpdate,
    LibroElectronicoRead,
)


def _norm_estado(val: Optional[str]) -> str:
    return (val or "").strip().casefold()


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


def _conflict_transicion() -> None:
    raise ConflictError(
        "No se puede completar la operación en el estado actual del libro.",
        internal_code="TAX_LIBRO_ESTADO_INVALIDO",
    )


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
    await get_empresa_servicio(client_id, data.empresa_id)
    dump = data.model_dump(exclude_none=True)
    dump.pop("estado", None)
    dump["estado"] = BORRADOR
    row = await _create(client_id, _dump_to_db(dump))
    return LibroElectronicoRead(**_row_to_read(row))


async def update_libro_electronico(
    client_id: UUID, libro_id: UUID, data: LibroElectronicoUpdate
) -> LibroElectronicoRead:
    row = await _get(client_id, libro_id)
    if not row:
        raise NotFoundError("Libro electrónico no encontrado")
    if _norm_estado(row.get("estado")) != BORRADOR:
        raise ConflictError(
            "Solo se permite actualizar un libro electrónico en estado borrador.",
            internal_code="TAX_LIBRO_NO_BORRADOR",
        )
    dump = data.model_dump(exclude_none=True)
    dump.pop("estado", None)
    if not dump:
        return LibroElectronicoRead(**_row_to_read(dict(row)))
    updated = await _update(client_id, libro_id, _dump_to_db(dump))
    if not updated:
        raise ConflictError(
            "No se pudo actualizar el libro (posible cambio concurrente de estado).",
            internal_code="TAX_LIBRO_UPDATE_CONFLICTO",
        )
    return LibroElectronicoRead(**_row_to_read(updated))


async def marcar_generado_libro_electronico(client_id: UUID, libro_id: UUID) -> LibroElectronicoRead:
    if not await _get(client_id, libro_id):
        raise NotFoundError("Libro electrónico no encontrado")
    row = await _transition(
        client_id,
        libro_id,
        frozenset({BORRADOR}),
        {"estado": GENERADO},
    )
    if not row:
        _conflict_transicion()
    return LibroElectronicoRead(**_row_to_read(row))


async def registrar_envio_libro_electronico(
    client_id: UUID, libro_id: UUID, body: LibroElectronicoRegistrarEnvio
) -> LibroElectronicoRead:
    if not await _get(client_id, libro_id):
        raise NotFoundError("Libro electrónico no encontrado")
    fecha = body.fecha_envio_sunat or datetime.now(timezone.utc).replace(tzinfo=None)
    extra: dict = {"estado": ENVIADO, "fecha_envio_sunat": fecha}
    if body.codigo_respuesta_sunat is not None:
        extra["codigo_respuesta_sunat"] = body.codigo_respuesta_sunat
    row = await _transition(
        client_id,
        libro_id,
        frozenset({GENERADO}),
        extra,
    )
    if not row:
        _conflict_transicion()
    return LibroElectronicoRead(**_row_to_read(row))


async def anular_libro_electronico(client_id: UUID, libro_id: UUID) -> LibroElectronicoRead:
    if not await _get(client_id, libro_id):
        raise NotFoundError("Libro electrónico no encontrado")
    row = await _transition(
        client_id,
        libro_id,
        ESTADOS_ANULABLES,
        {"estado": ANULADO},
    )
    if not row:
        _conflict_transicion()
    return LibroElectronicoRead(**_row_to_read(row))
