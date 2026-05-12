"""
Servicios de aplicación para fin_asiento_contable y fin_asiento_detalle.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from app.infrastructure.database.queries.fin import (
    list_asientos_contables as _list_asientos_contables,
    get_asiento_contable_by_id as _get_asiento_contable_by_id,
    create_asiento_contable as _create_asiento_contable,
    update_asiento_contable as _update_asiento_contable,
    list_asiento_detalles as _list_asiento_detalles,
    get_asiento_detalle_by_id as _get_asiento_detalle_by_id,
    create_asiento_detalle as _create_asiento_detalle,
    update_asiento_detalle as _update_asiento_detalle,
)
from app.infrastructure.database.queries.fin.periodo_contable_queries import (
    get_periodo_contable_by_id as _get_periodo_contable_by_id,
)
from app.infrastructure.database.queries.inv.moneda_queries import get_moneda_by_codigo
from app.modules.fin.presentation.schemas import (
    AsientoContableCreate,
    AsientoContableUpdate,
    AsientoContableRead,
    AsientoDetalleCreate,
    AsientoDetalleUpdate,
    AsientoDetalleRead,
)
from app.core.exceptions import NotFoundError, ServiceError


def _estado_norm(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _enrich_asiento_row(row: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(row)
    td, th = out.get("total_debe"), out.get("total_haber")
    d_td = Decimal(str(td)) if td is not None else Decimal(0)
    d_th = Decimal(str(th)) if th is not None else Decimal(0)
    diff = abs(d_td - d_th)
    if out.get("diferencia") is None:
        out["diferencia"] = diff
    if out.get("esta_cuadrado") is None:
        out["esta_cuadrado"] = bool(diff < Decimal("0.01"))
    return out


async def _resolver_moneda_id(
    client_id: UUID,
    *,
    moneda_id: Optional[UUID],
    moneda_codigo: Optional[str],
) -> UUID:
    if moneda_id is not None:
        return moneda_id
    codigo = (moneda_codigo or "PEN").strip().upper()
    mrow = await get_moneda_by_codigo(client_id=client_id, codigo=codigo)
    if not mrow:
        raise ServiceError(
            status_code=400,
            detail=f"Moneda con código '{codigo}' no encontrada en catálogo.",
            internal_code="FIN_MONEDA_NOT_FOUND",
        )
    return mrow["moneda_id"]


async def list_asientos_contables(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    periodo_id: Optional[UUID] = None,
    tipo_asiento: Optional[str] = None,
    estado: Optional[str] = None,
    modulo_origen: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    buscar: Optional[str] = None,
) -> List[AsientoContableRead]:
    """Lista asientos contables del tenant."""
    rows = await _list_asientos_contables(
        client_id=client_id,
        empresa_id=empresa_id,
        periodo_id=periodo_id,
        tipo_asiento=tipo_asiento,
        estado=estado,
        modulo_origen=modulo_origen,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar,
    )
    return [AsientoContableRead(**_enrich_asiento_row(r)) for r in rows]


async def get_asiento_contable_by_id(client_id: UUID, asiento_id: UUID) -> AsientoContableRead:
    """Obtiene un asiento contable por id. Lanza NotFoundError si no existe."""
    row = await _get_asiento_contable_by_id(client_id, asiento_id)
    if not row:
        raise NotFoundError(f"Asiento contable {asiento_id} no encontrado")
    return AsientoContableRead(**_enrich_asiento_row(row))


async def create_asiento_contable(client_id: UUID, data: AsientoContableCreate) -> AsientoContableRead:
    """Crea un asiento contable. Resuelve moneda_id desde cat_moneda si no viene en el body."""
    payload = data.model_dump(exclude_none=True)
    mid = await _resolver_moneda_id(
        client_id,
        moneda_id=payload.get("moneda_id"),
        moneda_codigo=payload.get("moneda"),
    )
    payload["moneda_id"] = mid
    row = await _create_asiento_contable(client_id, payload)
    return AsientoContableRead(**_enrich_asiento_row(row))


_PUT_FORBIDDEN_ASIENTO_KEYS = frozenset(
    {
        "estado",
        "aprobado_por_usuario_id",
        "fecha_aprobacion",
        "fecha_anulacion",
        "motivo_anulacion",
    }
)


async def update_asiento_contable(
    client_id: UUID, asiento_id: UUID, data: AsientoContableUpdate
) -> AsientoContableRead:
    """Actualiza un asiento solo en estado borrador. Transiciones de estado vía acciones dedicadas."""
    current = await _get_asiento_contable_by_id(client_id, asiento_id)
    if not current:
        raise NotFoundError(f"Asiento contable {asiento_id} no encontrado")
    if _estado_norm(current.get("estado")) != "borrador":
        raise ServiceError(
            status_code=400,
            detail="Solo se pueden editar asientos en estado borrador.",
            internal_code="FIN_ASIENTO_NOT_BORRADOR",
        )
    payload = data.model_dump(exclude_none=True)
    for k in _PUT_FORBIDDEN_ASIENTO_KEYS:
        payload.pop(k, None)
    if "moneda" in payload or "moneda_id" in payload:
        mid = await _resolver_moneda_id(
            client_id,
            moneda_id=payload.get("moneda_id"),
            moneda_codigo=payload.get("moneda") or current.get("moneda"),
        )
        payload["moneda_id"] = mid
    row = await _update_asiento_contable(client_id, asiento_id, payload)
    if not row:
        raise NotFoundError(f"Asiento contable {asiento_id} no encontrado")
    return AsientoContableRead(**_enrich_asiento_row(row))


async def aprobar_asiento_contable(
    client_id: UUID, asiento_id: UUID, aprobado_por_usuario_id: UUID
) -> AsientoContableRead:
    """borrador → aprobado."""
    current = await _get_asiento_contable_by_id(client_id, asiento_id)
    if not current:
        raise NotFoundError(f"Asiento contable {asiento_id} no encontrado")
    if _estado_norm(current.get("estado")) != "borrador":
        raise ServiceError(
            status_code=400,
            detail="Solo se pueden aprobar asientos en estado borrador.",
            internal_code="FIN_ASIENTO_APROBAR_INVALIDO",
        )
    row = await _update_asiento_contable(
        client_id,
        asiento_id,
        {
            "estado": "aprobado",
            "aprobado_por_usuario_id": aprobado_por_usuario_id,
            "fecha_aprobacion": datetime.utcnow(),
        },
    )
    if not row:
        raise NotFoundError(f"Asiento contable {asiento_id} no encontrado")
    return AsientoContableRead(**_enrich_asiento_row(row))


async def registrar_asiento_contable(client_id: UUID, asiento_id: UUID) -> AsientoContableRead:
    """aprobado → registrado."""
    current = await _get_asiento_contable_by_id(client_id, asiento_id)
    if not current:
        raise NotFoundError(f"Asiento contable {asiento_id} no encontrado")
    if _estado_norm(current.get("estado")) != "aprobado":
        raise ServiceError(
            status_code=400,
            detail="Solo se pueden registrar asientos en estado aprobado.",
            internal_code="FIN_ASIENTO_REGISTRAR_INVALIDO",
        )
    row = await _update_asiento_contable(client_id, asiento_id, {"estado": "registrado"})
    if not row:
        raise NotFoundError(f"Asiento contable {asiento_id} no encontrado")
    return AsientoContableRead(**_enrich_asiento_row(row))


async def anular_asiento_contable(
    client_id: UUID, asiento_id: UUID, motivo_anulacion: str
) -> AsientoContableRead:
    """
    Anula el asiento (cualquier estado salvo registrado).
    Requiere periodo contable abierto (no cerrado ni bloqueado).
    """
    current = await _get_asiento_contable_by_id(client_id, asiento_id)
    if not current:
        raise NotFoundError(f"Asiento contable {asiento_id} no encontrado")
    est = _estado_norm(current.get("estado"))
    if est == "registrado":
        raise ServiceError(
            status_code=400,
            detail="No se puede anular un asiento registrado.",
            internal_code="FIN_ASIENTO_ANULAR_REGISTRADO",
        )
    if est == "anulado":
        raise ServiceError(
            status_code=409,
            detail="El asiento ya está anulado.",
            internal_code="FIN_ASIENTO_YA_ANULADO",
        )
    periodo_id = current.get("periodo_id")
    if periodo_id:
        periodo = await _get_periodo_contable_by_id(client_id, periodo_id)
        if periodo:
            pest = _estado_norm(periodo.get("estado"))
            if pest in ("cerrado", "bloqueado"):
                raise ServiceError(
                    status_code=400,
                    detail="No se puede anular: el periodo contable está cerrado o bloqueado.",
                    internal_code="FIN_PERIODO_CERRADO",
                )
    row = await _update_asiento_contable(
        client_id,
        asiento_id,
        {
            "estado": "anulado",
            "motivo_anulacion": motivo_anulacion.strip(),
            "fecha_anulacion": datetime.utcnow(),
        },
    )
    if not row:
        raise NotFoundError(f"Asiento contable {asiento_id} no encontrado")
    return AsientoContableRead(**_enrich_asiento_row(row))


# ============================================================================
# DETALLES DE ASIENTO CONTABLE
# ============================================================================


async def _exigir_asiento_borrador(client_id: UUID, asiento_id: UUID) -> None:
    parent = await _get_asiento_contable_by_id(client_id, asiento_id)
    if not parent:
        raise NotFoundError(f"Asiento contable {asiento_id} no encontrado")
    if _estado_norm(parent.get("estado")) != "borrador":
        raise ServiceError(
            status_code=400,
            detail="Solo se permiten cambios en líneas cuando el asiento está en borrador.",
            internal_code="FIN_DETALLE_PADRE_NOT_BORRADOR",
        )


async def list_asiento_detalles(
    client_id: UUID,
    asiento_id: Optional[UUID] = None,
    cuenta_id: Optional[UUID] = None,
) -> List[AsientoDetalleRead]:
    """Lista detalles de asiento contable del tenant."""
    rows = await _list_asiento_detalles(
        client_id=client_id,
        asiento_id=asiento_id,
        cuenta_id=cuenta_id,
    )
    return [AsientoDetalleRead(**r) for r in rows]


async def get_asiento_detalle_by_id(client_id: UUID, asiento_detalle_id: UUID) -> AsientoDetalleRead:
    """Obtiene un detalle por id. Lanza NotFoundError si no existe."""
    row = await _get_asiento_detalle_by_id(client_id, asiento_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle de asiento contable {asiento_detalle_id} no encontrado")
    return AsientoDetalleRead(**row)


async def create_asiento_detalle(client_id: UUID, data: AsientoDetalleCreate) -> AsientoDetalleRead:
    """Crea un detalle; el asiento padre debe estar en borrador."""
    await _exigir_asiento_borrador(client_id, data.asiento_id)
    row = await _create_asiento_detalle(client_id, data.model_dump(exclude_none=True))
    return AsientoDetalleRead(**row)


async def update_asiento_detalle(
    client_id: UUID, asiento_detalle_id: UUID, data: AsientoDetalleUpdate
) -> AsientoDetalleRead:
    """Actualiza un detalle solo si el asiento padre está en borrador."""
    row_d = await _get_asiento_detalle_by_id(client_id, asiento_detalle_id)
    if not row_d:
        raise NotFoundError(f"Detalle de asiento contable {asiento_detalle_id} no encontrado")
    payload = data.model_dump(exclude_none=True)
    asiento_id = payload.get("asiento_id") or row_d["asiento_id"]
    await _exigir_asiento_borrador(client_id, asiento_id)
    row = await _update_asiento_detalle(client_id, asiento_detalle_id, payload)
    if not row:
        raise NotFoundError(f"Detalle de asiento contable {asiento_detalle_id} no encontrado")
    return AsientoDetalleRead(**row)
