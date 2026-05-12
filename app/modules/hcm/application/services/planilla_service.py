"""Servicios de aplicación para hcm_planilla."""
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.hcm import (
    list_planillas as _list,
    get_planilla_by_id as _get,
    create_planilla as _create,
    update_planilla as _update,
)
from app.modules.hcm.presentation.schemas import PlanillaCreate, PlanillaUpdate, PlanillaRead
from app.core.exceptions import ConflictError, NotFoundError

ESTADO_BORRADOR = "borrador"
ESTADO_CALCULADA = "calculada"
ESTADO_APROBADA = "aprobada"
ESTADO_PAGADA = "pagada"
ESTADO_CERRADA = "cerrada"


def _norm_estado(val: Optional[str]) -> str:
    return (val or "").strip().lower()


async def ensure_planilla_borrador(client_id: UUID, planilla_id: UUID) -> None:
    """Exige que la planilla exista y esté en borrador (mutaciones de detalle / líneas)."""
    row = await _get(client_id, planilla_id)
    if not row:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    if _norm_estado(row.get("estado")) != ESTADO_BORRADOR:
        raise ConflictError(
            "Solo se permiten cambios cuando la planilla está en estado borrador."
        )


async def list_planillas(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_planilla: Optional[str] = None,
    estado: Optional[str] = None,
    año: Optional[int] = None,
    mes: Optional[int] = None,
) -> List[PlanillaRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_planilla=tipo_planilla,
        estado=estado,
        año=año,
        mes=mes,
    )
    return [PlanillaRead(**r) for r in rows]


async def get_planilla_by_id(client_id: UUID, planilla_id: UUID) -> PlanillaRead:
    row = await _get(client_id, planilla_id)
    if not row:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    return PlanillaRead(**row)


async def create_planilla(client_id: UUID, data: PlanillaCreate) -> PlanillaRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return PlanillaRead(**row)


async def update_planilla(client_id: UUID, planilla_id: UUID, data: PlanillaUpdate) -> PlanillaRead:
    current = await _get(client_id, planilla_id)
    if not current:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    if _norm_estado(current.get("estado")) != ESTADO_BORRADOR:
        raise ConflictError(
            "Solo se puede editar la planilla mientras está en estado borrador."
        )
    row = await _update(client_id, planilla_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    return PlanillaRead(**row)


async def calcular_planilla(client_id: UUID, planilla_id: UUID) -> PlanillaRead:
    row = await _get(client_id, planilla_id)
    if not row:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    if _norm_estado(row.get("estado")) != ESTADO_BORRADOR:
        raise ConflictError("Solo se puede calcular una planilla en estado borrador.")
    updated = await _update(
        client_id, planilla_id, {"estado": ESTADO_CALCULADA}
    )
    if not updated:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    return PlanillaRead(**updated)


async def aprobar_planilla(
    client_id: UUID,
    planilla_id: UUID,
    aprobado_por_usuario_id: Optional[UUID] = None,
) -> PlanillaRead:
    row = await _get(client_id, planilla_id)
    if not row:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    if _norm_estado(row.get("estado")) != ESTADO_CALCULADA:
        raise ConflictError("Solo se puede aprobar una planilla en estado calculada.")
    payload = {
        "estado": ESTADO_APROBADA,
        "fecha_aprobacion": datetime.now(),
    }
    if aprobado_por_usuario_id is not None:
        payload["aprobado_por_usuario_id"] = aprobado_por_usuario_id
    updated = await _update(client_id, planilla_id, payload)
    if not updated:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    return PlanillaRead(**updated)


async def marcar_pagada_planilla(client_id: UUID, planilla_id: UUID) -> PlanillaRead:
    row = await _get(client_id, planilla_id)
    if not row:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    if _norm_estado(row.get("estado")) != ESTADO_APROBADA:
        raise ConflictError("Solo se puede marcar como pagada una planilla en estado aprobada.")
    payload: dict = {"estado": ESTADO_PAGADA}
    if row.get("fecha_pago") is None:
        payload["fecha_pago"] = date.today()
    updated = await _update(client_id, planilla_id, payload)
    if not updated:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    return PlanillaRead(**updated)


async def cerrar_planilla(client_id: UUID, planilla_id: UUID) -> PlanillaRead:
    row = await _get(client_id, planilla_id)
    if not row:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    if _norm_estado(row.get("estado")) != ESTADO_PAGADA:
        raise ConflictError("Solo se puede cerrar una planilla en estado pagada.")
    updated = await _update(
        client_id, planilla_id, {"estado": ESTADO_CERRADA}
    )
    if not updated:
        raise NotFoundError(f"Planilla {planilla_id} no encontrada")
    return PlanillaRead(**updated)
