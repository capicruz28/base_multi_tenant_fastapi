"""
Helpers de estorno de movimientos INV (P0-003).

Espejo compensatorio, gates MVP, idempotencia y gate X-08 pre-PPM.
Sin modificar lógica funcional de procesar_movimiento_servicio.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional
from uuid import UUID
import uuid
from datetime import datetime

from sqlalchemy import and_, select

from app.core.application.unit_of_work import UnitOfWork
from app.core.exceptions import ConflictError
from app.infrastructure.database.queries.inv import get_stock_by_producto_almacen
from app.infrastructure.database.tables_erp import InvMovimientoTable

ESTORNO_REF_TIPO = "movimiento_estorno"
ESTORNO_MVP_BLOCKED_REF_TIPOS = frozenset({"inventario_fisico", "recepcion"})
MOVIMIENTO_YA_ESTORNADO_CODE = "MOVIMIENTO_YA_ESTORNADO"
ESTORNO_INTEGRACION_NO_MVP_CODE = "ESTORNO_INTEGRACION_NO_MVP"
ESTORNO_ENTRADA_PPM_QNEW_CERO_CODE = "ESTORNO_ENTRADA_PPM_QNEW_CERO"
ESTORNO_NO_PROCESADO_CODE = "ESTORNO_NO_PROCESADO"
ESTORNO_UPDATE_RACE_CODE = "ESTORNO_UPDATE_RACE"

SQL_LOCK_MOVIMIENTO_ORIGINAL = """
SELECT *
FROM inv_movimiento WITH (UPDLOCK, ROWLOCK)
WHERE cliente_id = :cliente_id
  AND empresa_id = :empresa_id
  AND movimiento_id = :movimiento_id
"""

_MSG_YA_ESTORNADO = "El movimiento ya fue estornado o existe un compensatorio vinculado."
_MSG_INTEGRACION_NO_MVP = (
    "El estorno de movimientos generados por inventario físico o recepción "
    "no está disponible en esta versión."
)
_MSG_ENTRADA_PPM_QNEW_CERO = (
    "No se puede estornar: la reversión dejaría el stock en cero con un tipo de "
    "entrada que afecta costo. Ajuste el stock manualmente o use un movimiento "
    "de ajuste antes de estornar."
)
_MSG_NO_PROCESADO = (
    "Solo se puede estornar un movimiento en estado 'procesado'. "
    "Estado actual: '{estado}'."
)
_MSG_UPDATE_RACE = (
    "No se pudo marcar el movimiento como estornado: fue modificado concurrentemente."
)


def gen_numero_movimiento_estorno() -> str:
    stamp = datetime.utcnow().strftime("%y%m%d")
    micro = datetime.utcnow().strftime("%f")[-4:]
    return f"INV-EST-{stamp}-{micro}"[:20]


def _to_decimal(value: Any, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _norm_clase(clase: Optional[str]) -> str:
    return (clase or "").strip().lower()


def _norm_ref_tipo(ref_tipo: Optional[str]) -> str:
    return (ref_tipo or "").strip().lower()


def _afecta_costo_from_tipo(tipo_movimiento: dict) -> bool:
    raw = tipo_movimiento.get("afecta_costo")
    if raw is None:
        return True
    return bool(raw)


def assert_estorno_mvp_allowed(mov: dict) -> None:
    """Gate P0b: bloquea orígenes de integración fuera de MVP."""
    ref = _norm_ref_tipo(mov.get("documento_referencia_tipo"))
    if ref in ESTORNO_MVP_BLOCKED_REF_TIPOS:
        raise ConflictError(
            detail=_MSG_INTEGRACION_NO_MVP,
            internal_code=ESTORNO_INTEGRACION_NO_MVP_CODE,
        )


def assert_not_already_estornado(mov: dict) -> None:
    """Rechaza movimientos en estado terminal estornado."""
    estado = (mov.get("estado") or "").strip().lower()
    if estado == "estornado":
        raise ConflictError(
            detail=_MSG_YA_ESTORNADO,
            internal_code=MOVIMIENTO_YA_ESTORNADO_CODE,
        )


async def find_compensatorio_by_original(
    uow: UnitOfWork,
    *,
    client_id: UUID,
    empresa_id: UUID,
    original_movimiento_id: UUID,
) -> Optional[dict]:
    """Idempotencia P1: busca compensatorio vinculado al original."""
    rows = await uow.execute(
        select(InvMovimientoTable).where(
            and_(
                InvMovimientoTable.c.cliente_id == client_id,
                InvMovimientoTable.c.empresa_id == empresa_id,
                InvMovimientoTable.c.documento_referencia_tipo == ESTORNO_REF_TIPO,
                InvMovimientoTable.c.documento_referencia_id == original_movimiento_id,
            )
        )
    )
    return rows[0] if rows else None


def assert_compensatorio_no_existe(compensatorio: Optional[dict]) -> None:
    """P1: 409 si ya existe compensatorio para el original."""
    if compensatorio is not None:
        raise ConflictError(
            detail=_MSG_YA_ESTORNADO,
            internal_code=MOVIMIENTO_YA_ESTORNADO_CODE,
        )


async def assert_entrada_espejo_ppm_viable(
    *,
    client_id: UUID,
    empresa_id: UUID,
    tipo_movimiento: dict,
    movimiento: dict,
    detalles: list[dict],
) -> None:
    """
    Gate P0c — X-08 §7.6.

    Detecta reversión total de entrada costeable que dejaría q_new=0 en PPM,
    antes de INSERT compensatorio o invocar procesar.
    """
    clase = _norm_clase(tipo_movimiento.get("clase_movimiento"))
    if clase != "entrada":
        return
    if not _afecta_costo_from_tipo(tipo_movimiento):
        return

    almacen_destino_id = movimiento.get("almacen_destino_id")
    if not almacen_destino_id:
        return

    for det in detalles:
        producto_id = det.get("producto_id")
        if not producto_id:
            continue

        qty_original = _to_decimal(det.get("cantidad_base"))
        if qty_original == 0:
            continue

        qty_espejo = -qty_original
        stock = await get_stock_by_producto_almacen(
            client_id=client_id,
            empresa_id=empresa_id,
            producto_id=producto_id,
            almacen_id=almacen_destino_id,
        )
        if not stock:
            continue

        q_actual = _to_decimal(stock.get("cantidad_actual"))
        if q_actual + qty_espejo == 0:
            raise ConflictError(
                detail=_MSG_ENTRADA_PPM_QNEW_CERO,
                internal_code=ESTORNO_ENTRADA_PPM_QNEW_CERO_CODE,
            )


def _mirror_cantidad_base(cantidad_base: Decimal, clase: str) -> Decimal:
    if _norm_clase(clase) == "transferencia":
        return cantidad_base
    return -cantidad_base


def build_compensatorio_detalles(
    original_detalles: list[dict],
    clase_movimiento: str,
) -> list[dict]:
    """Construye líneas espejo §7.1 para INSERT en P3."""
    clase = _norm_clase(clase_movimiento)
    resultado: list[dict] = []

    for det in original_detalles:
        cantidad_base = _to_decimal(det.get("cantidad_base"))
        if cantidad_base == 0:
            continue

        cantidad = _to_decimal(det.get("cantidad"), str(cantidad_base))
        cantidad_espejo = _mirror_cantidad_base(cantidad_base, clase)
        factor = (
            Decimal("1")
            if cantidad_base == 0
            else cantidad_espejo / cantidad_base
        )
        cantidad_linea = cantidad * factor

        resultado.append(
            {
                "movimiento_detalle_id": uuid.uuid4(),
                "producto_id": det.get("producto_id"),
                "cantidad": cantidad_linea,
                "unidad_medida_id": det.get("unidad_medida_id"),
                "cantidad_base": cantidad_espejo,
                "costo_unitario": _to_decimal(det.get("costo_unitario")),
                "moneda_id": det.get("moneda_id"),
                "moneda": det.get("moneda"),
                "lote": det.get("lote"),
                "fecha_vencimiento": det.get("fecha_vencimiento"),
                "numero_serie": det.get("numero_serie"),
                "ubicacion_almacen": det.get("ubicacion_almacen"),
                "observaciones": det.get("observaciones"),
            }
        )

    return resultado


def build_compensatorio_cabecera(
    *,
    original: dict,
    motivo: Optional[str],
    usuario_estorno: UUID,
    compensatorio_movimiento_id: UUID,
    numero_movimiento: str,
    detalles_espejo: list[dict],
    now: Optional[datetime] = None,
) -> dict:
    """Construye cabecera compensatorio §5.1 + X-07. Almacenes deben venir ya espejados."""
    ts = now or datetime.utcnow()

    total_cantidad = sum(
        abs(_to_decimal(d.get("cantidad_base"))) for d in detalles_espejo
    )
    total_costo = sum(
        abs(_to_decimal(d.get("cantidad_base")))
        * _to_decimal(d.get("costo_unitario"))
        for d in detalles_espejo
    )

    numero_original = original.get("numero_movimiento") or ""
    obs_partes = [f"Estorno de {numero_original}"]
    if motivo and motivo.strip():
        obs_partes.append(motivo.strip())
    observaciones = " — ".join(obs_partes)

    cab: dict = {
        "movimiento_id": compensatorio_movimiento_id,
        "cliente_id": original.get("cliente_id"),
        "empresa_id": original.get("empresa_id"),
        "numero_movimiento": numero_movimiento,
        "tipo_movimiento_id": original.get("tipo_movimiento_id"),
        "fecha_movimiento": ts,
        "fecha_contable": original.get("fecha_contable") or ts.date(),
        "almacen_origen_id": original.get("almacen_origen_id"),
        "almacen_destino_id": original.get("almacen_destino_id"),
        "modulo_origen": "INV",
        "documento_referencia_tipo": ESTORNO_REF_TIPO,
        "documento_referencia_id": original.get("movimiento_id"),
        "documento_referencia_numero": numero_original,
        "tercero_tipo": original.get("tercero_tipo"),
        "tercero_id": original.get("tercero_id"),
        "tercero_nombre": original.get("tercero_nombre"),
        "total_items": len(detalles_espejo),
        "total_cantidad": total_cantidad,
        "total_costo": total_costo,
        "moneda_id": original.get("moneda_id"),
        "requiere_autorizacion": original.get("requiere_autorizacion"),
        "observaciones": observaciones,
        "centro_costo_id": original.get("centro_costo_id"),
        "usuario_creacion_id": usuario_estorno,
        "fecha_actualizacion": ts,
    }

    if bool(original.get("requiere_autorizacion")):
        cab["estado"] = "autorizado"
        cab["fecha_autorizacion"] = ts
        cab["autorizado_por_usuario_id"] = usuario_estorno
    else:
        cab["estado"] = "borrador"
        cab["fecha_autorizacion"] = None
        cab["autorizado_por_usuario_id"] = None

    return cab


def build_compensatorio_almacenes(
    original: dict,
    clase_movimiento: str,
) -> tuple[Optional[UUID], Optional[UUID]]:
    """Devuelve (almacen_origen_id, almacen_destino_id) espejo para cabecera."""
    clase = _norm_clase(clase_movimiento)
    origen = original.get("almacen_origen_id")
    destino = original.get("almacen_destino_id")

    if clase == "transferencia":
        return destino, origen
    if clase == "entrada":
        return None, destino
    if clase == "salida":
        return origen, None
    if clase == "ajuste":
        target = destino or origen
        if target == destino and destino is not None:
            return None, destino
        return origen, None
    return origen, destino


def build_compensatorio_cabecera_espejo(
    *,
    original: dict,
    clase_movimiento: str,
    motivo: Optional[str],
    usuario_estorno: UUID,
    compensatorio_movimiento_id: UUID,
    numero_movimiento: str,
    detalles_espejo: list[dict],
    now: Optional[datetime] = None,
) -> dict:
    """Cabecera compensatorio con almacenes espejo aplicados."""
    almacen_origen_id, almacen_destino_id = build_compensatorio_almacenes(
        original, clase_movimiento
    )
    original_espejo = dict(original)
    original_espejo["almacen_origen_id"] = almacen_origen_id
    original_espejo["almacen_destino_id"] = almacen_destino_id
    return build_compensatorio_cabecera(
        original=original_espejo,
        motivo=motivo,
        usuario_estorno=usuario_estorno,
        compensatorio_movimiento_id=compensatorio_movimiento_id,
        numero_movimiento=numero_movimiento,
        detalles_espejo=detalles_espejo,
        now=now,
    )
