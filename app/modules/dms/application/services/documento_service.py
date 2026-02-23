"""Servicio aplicacion dms_documento. Convierte tamano_bytes <-> tamaño_bytes."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.dms import (
    list_documento as _list,
    get_documento_by_id as _get,
    create_documento as _create,
    update_documento as _update,
)
from app.modules.dms.presentation.schemas import (
    DocumentoCreate,
    DocumentoUpdate,
    DocumentoRead,
)
from app.core.exceptions import NotFoundError


def _row_to_read(row: dict) -> dict:
    r = dict(row)
    if "tamaño_bytes" in r:
        r["tamano_bytes"] = r.pop("tamaño_bytes", None)
    return r


def _dump_to_db(data: dict) -> dict:
    d = dict(data)
    if "tamano_bytes" in d:
        d["tamaño_bytes"] = d.pop("tamano_bytes")
    return d


async def list_documento(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_documento: Optional[str] = None,
    categoria: Optional[str] = None,
    estado: Optional[str] = None,
    entidad_tipo: Optional[str] = None,
    entidad_id: Optional[UUID] = None,
    carpeta: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[DocumentoRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_documento=tipo_documento,
        categoria=categoria,
        estado=estado,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        carpeta=carpeta,
        buscar=buscar,
    )
    return [DocumentoRead(**_row_to_read(r)) for r in rows]


async def get_documento_by_id(client_id: UUID, documento_id: UUID) -> DocumentoRead:
    row = await _get(client_id, documento_id)
    if not row:
        raise NotFoundError("Documento no encontrado")
    return DocumentoRead(**_row_to_read(row))


async def create_documento(client_id: UUID, data: DocumentoCreate) -> DocumentoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, _dump_to_db(dump))
    return DocumentoRead(**_row_to_read(row))


async def update_documento(
    client_id: UUID, documento_id: UUID, data: DocumentoUpdate
) -> DocumentoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _update(client_id, documento_id, _dump_to_db(dump))
    if not row:
        raise NotFoundError("Documento no encontrado")
    return DocumentoRead(**_row_to_read(row))
