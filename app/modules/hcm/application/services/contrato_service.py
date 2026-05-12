"""Servicios de aplicación para hcm_contrato."""
from datetime import date
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.hcm import (
    list_contratos as _list,
    get_contrato_by_id as _get,
    create_contrato as _create,
    update_contrato as _update,
)
from app.modules.hcm.presentation.schemas import ContratoCreate, ContratoUpdate, ContratoRead
from app.core.exceptions import ConflictError, NotFoundError


def _norm_estado_contrato(val: Optional[str]) -> str:
    return (val or "").strip().lower()


async def list_contratos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    empleado_id: Optional[UUID] = None,
    estado_contrato: Optional[str] = None,
    es_contrato_vigente: Optional[bool] = None,
) -> List[ContratoRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        empleado_id=empleado_id,
        estado_contrato=estado_contrato,
        es_contrato_vigente=es_contrato_vigente,
    )
    return [ContratoRead(**r) for r in rows]


async def get_contrato_by_id(client_id: UUID, contrato_id: UUID) -> ContratoRead:
    row = await _get(client_id, contrato_id)
    if not row:
        raise NotFoundError(f"Contrato {contrato_id} no encontrado")
    return ContratoRead(**row)


async def create_contrato(client_id: UUID, data: ContratoCreate) -> ContratoRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return ContratoRead(**row)


async def update_contrato(client_id: UUID, contrato_id: UUID, data: ContratoUpdate) -> ContratoRead:
    row = await _update(client_id, contrato_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Contrato {contrato_id} no encontrado")
    return ContratoRead(**row)


async def rescindir_contrato(
    client_id: UUID,
    contrato_id: UUID,
    fecha_rescision: Optional[date] = None,
    motivo_rescision: Optional[str] = None,
) -> ContratoRead:
    """Marca el contrato como rescindido; fecha de fin operativa = fecha de rescisión."""
    row = await _get(client_id, contrato_id)
    if not row:
        raise NotFoundError(f"Contrato {contrato_id} no encontrado")
    if _norm_estado_contrato(row.get("estado_contrato")) == "rescindido":
        raise ConflictError("El contrato ya está rescindido.")
    fr = fecha_rescision or date.today()
    payload = {
        "estado_contrato": "rescindido",
        "fecha_rescision": fr,
        "fecha_fin": fr,
        "es_contrato_vigente": False,
    }
    if motivo_rescision is not None:
        payload["motivo_rescision"] = motivo_rescision
    updated = await _update(client_id, contrato_id, payload)
    if not updated:
        raise NotFoundError(f"Contrato {contrato_id} no encontrado")
    return ContratoRead(**updated)
