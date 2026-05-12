"""Servicio aplicación mps_plan_produccion_detalle. Calcula porcentaje_uso_capacidad si aplica."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.infrastructure.database.queries.mps import (
    list_plan_produccion_detalle as _list,
    get_plan_produccion_detalle_by_id as _get,
    create_plan_produccion_detalle as _create,
    update_plan_produccion_detalle as _update,
)
from app.modules.mps.presentation.schemas import (
    PlanProduccionDetalleCreate,
    PlanProduccionDetalleUpdate,
    PlanProduccionDetalleRead,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.queries.mps.plan_produccion_queries import get_plan_produccion_by_id as _get_plan


def _enrich_detalle(row: dict) -> dict:
    r = dict(row)
    cap = r.get("capacidad_disponible") or Decimal("0")
    qty = r.get("cantidad_planificada") or Decimal("0")
    if cap and cap > 0:
        r["porcentaje_uso_capacidad"] = (qty / cap) * 100
    else:
        r["porcentaje_uso_capacidad"] = None
    return r


async def list_plan_produccion_detalle(
    client_id: UUID,
    plan_produccion_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[PlanProduccionDetalleRead]:
    rows = await _list(
        client_id=client_id,
        plan_produccion_id=plan_produccion_id,
        producto_id=producto_id,
    )
    return [PlanProduccionDetalleRead(**_enrich_detalle(r)) for r in rows]


async def get_plan_produccion_detalle_by_id(
    client_id: UUID, plan_detalle_id: UUID
) -> PlanProduccionDetalleRead:
    row = await _get(client_id, plan_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle plan producción {plan_detalle_id} no encontrado")
    # Validación de coherencia tenant: el plan debe existir y empresa_id debe coincidir
    plan = await _get_plan(client_id, row.get("plan_produccion_id"))
    if not plan:
        raise NotFoundError(f"Plan de producción {row.get('plan_produccion_id')} no encontrado")
    if row.get("empresa_id") != plan.get("empresa_id"):
        raise ValidationError(
            detail="Inconsistencia: el detalle pertenece a una empresa distinta a la cabecera",
            internal_code="MPS_PLAN_DETALLE_EMPRESA_MISMATCH",
        )
    return PlanProduccionDetalleRead(**_enrich_detalle(row))


async def create_plan_produccion_detalle(
    client_id: UUID, data: PlanProduccionDetalleCreate
) -> PlanProduccionDetalleRead:
    dump = data.model_dump(exclude_none=True)
    plan_id = dump.get("plan_produccion_id")
    if not plan_id:
        raise ValidationError(detail="plan_produccion_id es obligatorio", internal_code="MPS_PLAN_ID_REQUIRED")

    plan = await _get_plan(client_id, plan_id)
    if not plan:
        raise NotFoundError(f"Plan de producción {plan_id} no encontrado")

    estado = (plan.get("estado") or "borrador").strip().lower()
    if estado != "borrador":
        raise ValidationError(
            detail=f"No se puede modificar detalle si el plan no está en borrador (estado actual: {estado})",
            internal_code="MPS_PLAN_NOT_EDITABLE",
        )

    empresa_id = plan.get("empresa_id")
    if not empresa_id:
        raise ValidationError(
            detail="El plan de producción no tiene empresa_id (inconsistencia de datos)",
            internal_code="MPS_PLAN_EMPRESA_MISSING",
        )

    # ✅ No tomar empresa_id del body: se deriva desde cabecera (tenant-safe)
    dump["empresa_id"] = empresa_id
    row = await _create(client_id, dump)
    return PlanProduccionDetalleRead(**_enrich_detalle(row))


async def update_plan_produccion_detalle(
    client_id: UUID, plan_detalle_id: UUID, data: PlanProduccionDetalleUpdate
) -> PlanProduccionDetalleRead:
    actual = await _get(client_id, plan_detalle_id)
    if not actual:
        raise NotFoundError(f"Detalle plan producción {plan_detalle_id} no encontrado")

    dump = data.model_dump(exclude_none=True)

    plan_id = dump.get("plan_produccion_id") or actual.get("plan_produccion_id")
    if not plan_id:
        raise ValidationError(
            detail="No se pudo determinar plan_produccion_id del detalle",
            internal_code="MPS_PLAN_ID_REQUIRED",
        )

    plan = await _get_plan(client_id, plan_id)
    if not plan:
        raise NotFoundError(f"Plan de producción {plan_id} no encontrado")

    estado = (plan.get("estado") or "borrador").strip().lower()
    if estado != "borrador":
        raise ValidationError(
            detail=f"No se puede modificar detalle si el plan no está en borrador (estado actual: {estado})",
            internal_code="MPS_PLAN_NOT_EDITABLE",
        )

    empresa_id = plan.get("empresa_id")
    if not empresa_id:
        raise ValidationError(
            detail="El plan de producción no tiene empresa_id (inconsistencia de datos)",
            internal_code="MPS_PLAN_EMPRESA_MISSING",
        )
    dump["empresa_id"] = empresa_id

    row = await _update(client_id, plan_detalle_id, dump)
    if not row:
        raise NotFoundError(f"Detalle plan producción {plan_detalle_id} no encontrado")
    return PlanProduccionDetalleRead(**_enrich_detalle(row))
