"""
Servicios de aplicación para pos_turno_caja.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError
from app.infrastructure.database.queries.pos import (
    list_turnos_caja as _list_turnos_caja,
    get_turno_caja_by_id as _get_turno_caja_by_id,
    create_turno_caja as _create_turno_caja,
    update_turno_caja as _update_turno_caja,
    summarize_ventas_por_turno as _summarize_ventas_por_turno,
)
from app.modules.pos.presentation.schemas import (
    TurnoCajaCreate,
    TurnoCajaCerrarRequest,
    TurnoCajaUpdate,
    TurnoCajaRead,
)


def _norm_estado(val: Optional[str]) -> str:
    return (val or "").strip().lower()


def _dec(val) -> Decimal:
    if val is None:
        return Decimal("0")
    return Decimal(str(val))


async def list_turnos_caja(
    client_id: UUID,
    punto_venta_id: Optional[UUID] = None,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    cajero_usuario_id: Optional[UUID] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> List[TurnoCajaRead]:
    """Lista turnos de caja del tenant."""
    rows = await _list_turnos_caja(
        client_id=client_id,
        punto_venta_id=punto_venta_id,
        empresa_id=empresa_id,
        estado=estado,
        cajero_usuario_id=cajero_usuario_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return [TurnoCajaRead(**row) for row in rows]


async def get_turno_caja_by_id(
    client_id: UUID,
    turno_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> TurnoCajaRead:
    """Obtiene un turno de caja por id."""
    row = await _get_turno_caja_by_id(client_id, turno_id, empresa_id=empresa_id)
    if not row:
        raise NotFoundError(f"Turno de caja {turno_id} no encontrado")
    return TurnoCajaRead(**row)


async def create_turno_caja(client_id: UUID, data: TurnoCajaCreate) -> TurnoCajaRead:
    """Crea un turno de caja (apertura)."""
    row = await _create_turno_caja(client_id, data.model_dump(exclude_none=True))
    return TurnoCajaRead(**row)


async def update_turno_caja(
    client_id: UUID,
    turno_id: UUID,
    data: TurnoCajaUpdate,
    empresa_id: Optional[UUID] = None,
) -> TurnoCajaRead:
    """Actualiza un turno de caja (no incluye totales del sistema)."""
    payload = data.model_dump(exclude_none=True)
    row = await _update_turno_caja(
        client_id, turno_id, payload, empresa_id=empresa_id
    )
    if not row:
        raise NotFoundError(f"Turno de caja {turno_id} no encontrado")
    return TurnoCajaRead(**row)


async def cerrar_turno_caja(
    client_id: UUID,
    turno_id: UUID,
    data: TurnoCajaCerrarRequest,
    cerrado_por_usuario_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> TurnoCajaRead:
    """
    Cierra el turno: recalcula totales desde ventas del turno, fija monto esperado
    de efectivo y el conteo real informado.
    """
    turn = await _get_turno_caja_by_id(client_id, turno_id, empresa_id=empresa_id)
    if not turn:
        raise NotFoundError(f"Turno de caja {turno_id} no encontrado")
    if _norm_estado(turn.get("estado")) != "abierto":
        raise ValidationError(
            "El turno no está abierto; no se puede cerrar.",
            internal_code="POS_TURNO_NO_ABIERTO",
        )

    ag = await _summarize_ventas_por_turno(client_id, turno_id)
    sum_ef = _dec(ag.get("sum_efectivo"))
    sum_tj = _dec(ag.get("sum_tarjeta"))
    sum_tr = _dec(ag.get("sum_transferencia"))
    sum_ot = _dec(ag.get("sum_otros"))
    monto_apertura = _dec(turn.get("monto_apertura"))
    egresos = _dec(turn.get("total_egresos"))
    monto_cierre_esperado = monto_apertura + sum_ef - egresos

    cierre_payload = {
        "fecha_cierre": datetime.utcnow(),
        "estado": "cerrado",
        "total_ventas": int(ag.get("n_ventas") or 0),
        "total_ventas_efectivo": sum_ef,
        "total_ventas_tarjeta": sum_tj,
        "total_ventas_transferencia": sum_tr,
        "total_ventas_otros": sum_ot,
        "total_facturas": int(ag.get("n_facturas") or 0),
        "total_boletas": int(ag.get("n_boletas") or 0),
        "total_notas_credito": int(ag.get("n_notas_credito") or 0),
        "monto_cierre_esperado": monto_cierre_esperado,
        "monto_cierre_real": data.monto_cierre_real,
        "observaciones_cierre": data.observaciones_cierre,
        "cerrado_por_usuario_id": cerrado_por_usuario_id,
    }
    row = await _update_turno_caja(
        client_id, turno_id, cierre_payload, empresa_id=empresa_id
    )
    if not row:
        raise NotFoundError(f"Turno de caja {turno_id} no encontrado")
    return TurnoCajaRead(**row)
