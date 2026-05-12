"""Servicio aplicación mnt_orden_trabajo. Calcula duracion_horas y costo_total si aplica.

Workflow de estados (mnt_orden_trabajo.estado):
    solicitada -> programada -> en_proceso -> completada -> cerrada
                                |    ^
                                v    |
                              pausada
    Transición transversal: cualquier estado (excepto cerrada/cancelada) -> cancelada

El cierre (completada -> cerrada) es transaccional:
    1) UPDATE mnt_orden_trabajo (estado, fecha_cierre, cerrado_por_usuario_id, calificacion_trabajo)
    2) INSERT mnt_historial_mantenimiento (bitácora derivada)
    3) UPDATE mnt_plan_mantenimiento (fecha_ultimo_mantenimiento + fecha_proximo_mantenimiento) si aplica
    Todo dentro de un único UnitOfWork (BEGIN / COMMIT / ROLLBACK).
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Set
from uuid import UUID
from decimal import Decimal
from datetime import datetime, date, timedelta

from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.queries.mnt import (
    list_orden_trabajo as _list,
    get_orden_trabajo_by_id as _get,
    create_orden_trabajo as _create,
    update_orden_trabajo as _update,
)
from app.infrastructure.database.tables_erp import (
    MntOrdenTrabajoTable,
    MntHistorialMantenimientoTable,
    MntPlanMantenimientoTable,
)
from app.core.application.unit_of_work import unit_of_work
from app.modules.mnt.presentation.schemas import OrdenTrabajoCreate, OrdenTrabajoUpdate, OrdenTrabajoRead
from app.core.exceptions import NotFoundError, ConflictError


# --------------------------------------------------------------------------
# Estados y reglas de transición
# --------------------------------------------------------------------------
ESTADOS_EDITABLES_PUT: Set[str] = {"solicitada", "programada"}
ESTADO_FINAL_CERRADA: str = "cerrada"
ESTADO_CANCELADA: str = "cancelada"

# Estado de origen permitido para cada transición -> estado destino
_TRANSICIONES: Dict[str, Dict[str, Any]] = {
    "programar": {"from": {"solicitada"}, "to": "programada"},
    "iniciar":   {"from": {"programada"}, "to": "en_proceso"},
    "pausar":    {"from": {"en_proceso"}, "to": "pausada"},
    "reanudar":  {"from": {"pausada"}, "to": "en_proceso"},
    "completar": {"from": {"en_proceso"}, "to": "completada"},
}
# 'cancelar' acepta cualquier estado actual EXCEPTO los terminales
_ESTADOS_NO_CANCELABLES: Set[str] = {"cerrada", "cancelada"}


def _enrich_ot(row: dict) -> dict:
    r = dict(row)
    fi = r.get("fecha_inicio_real")
    ff = r.get("fecha_fin_real")
    if fi and ff:
        if isinstance(fi, datetime) and isinstance(ff, datetime):
            delta = ff - fi
            r["duracion_horas"] = Decimal(str(round(delta.total_seconds() / 3600, 2)))
        else:
            r["duracion_horas"] = None
    else:
        r["duracion_horas"] = None
    co = r.get("costo_mano_obra") or Decimal("0")
    cr = r.get("costo_repuestos") or Decimal("0")
    cs = r.get("costo_servicios_terceros") or Decimal("0")
    r["costo_total"] = co + cr + cs
    return r


def _normaliza_estado(estado: Optional[str]) -> str:
    return (estado or "").strip().lower()


# --------------------------------------------------------------------------
# CRUD básico
# --------------------------------------------------------------------------
async def list_orden_trabajo(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    activo_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    tipo_mantenimiento: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[OrdenTrabajoRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        activo_id=activo_id,
        estado=estado,
        tipo_mantenimiento=tipo_mantenimiento,
        buscar=buscar,
    )
    return [OrdenTrabajoRead(**_enrich_ot(r)) for r in rows]


async def get_orden_trabajo_by_id(client_id: UUID, orden_trabajo_id: UUID) -> OrdenTrabajoRead:
    row = await _get(client_id, orden_trabajo_id)
    if not row:
        raise NotFoundError(f"Orden de trabajo {orden_trabajo_id} no encontrada")
    return OrdenTrabajoRead(**_enrich_ot(row))


async def create_orden_trabajo(client_id: UUID, data: OrdenTrabajoCreate) -> OrdenTrabajoRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return OrdenTrabajoRead(**_enrich_ot(row))


async def update_orden_trabajo(
    client_id: UUID, orden_trabajo_id: UUID, data: OrdenTrabajoUpdate
) -> OrdenTrabajoRead:
    # Validación de estado: la OT solo es editable cuando está en 'solicitada' o 'programada'
    current = await _get(client_id, orden_trabajo_id)
    if not current:
        raise NotFoundError(f"Orden de trabajo {orden_trabajo_id} no encontrada")
    estado_actual = _normaliza_estado(current.get("estado"))
    if estado_actual not in ESTADOS_EDITABLES_PUT:
        raise ConflictError(
            detail=(
                f"No se puede actualizar la OT en estado '{estado_actual}'. "
                f"Solo es editable en {sorted(ESTADOS_EDITABLES_PUT)}. "
                f"Use los endpoints de transición de estado para flujos posteriores."
            ),
            internal_code="MNT_OT_NOT_EDITABLE",
        )
    row = await _update(client_id, orden_trabajo_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Orden de trabajo {orden_trabajo_id} no encontrada")
    return OrdenTrabajoRead(**_enrich_ot(row))


# --------------------------------------------------------------------------
# Helpers internos de transición
# --------------------------------------------------------------------------
async def _aplicar_transicion(
    client_id: UUID,
    orden_trabajo_id: UUID,
    accion: str,
    extra_values: Optional[Dict[str, Any]] = None,
) -> OrdenTrabajoRead:
    """Aplica una transición simple validando estado origen permitido."""
    cfg = _TRANSICIONES[accion]
    estados_origen: Set[str] = cfg["from"]
    estado_destino: str = cfg["to"]

    current = await _get(client_id, orden_trabajo_id)
    if not current:
        raise NotFoundError(f"Orden de trabajo {orden_trabajo_id} no encontrada")
    estado_actual = _normaliza_estado(current.get("estado"))
    if estado_actual not in estados_origen:
        raise ConflictError(
            detail=(
                f"No se puede '{accion}' una OT en estado '{estado_actual}'. "
                f"Estado(s) origen permitido(s): {sorted(estados_origen)}."
            ),
            internal_code=f"MNT_OT_TRANSITION_INVALID_{accion.upper()}",
        )

    payload: Dict[str, Any] = {"estado": estado_destino}
    if extra_values:
        payload.update(extra_values)

    row = await _update(client_id, orden_trabajo_id, payload)
    if not row:
        raise NotFoundError(f"Orden de trabajo {orden_trabajo_id} no encontrada")
    return OrdenTrabajoRead(**_enrich_ot(row))


# --------------------------------------------------------------------------
# Transiciones públicas (no transaccional): programar / iniciar / pausar /
# reanudar / completar / cancelar
# --------------------------------------------------------------------------
async def programar_orden_trabajo(
    client_id: UUID,
    orden_trabajo_id: UUID,
    fecha_programada: Optional[datetime] = None,
    tecnico_asignado_usuario_id: Optional[UUID] = None,
    tecnico_nombre: Optional[str] = None,
) -> OrdenTrabajoRead:
    """`solicitada` -> `programada`. Permite asignar fecha programada y técnico."""
    extra: Dict[str, Any] = {}
    if fecha_programada is not None:
        extra["fecha_programada"] = fecha_programada
    if tecnico_asignado_usuario_id is not None:
        extra["tecnico_asignado_usuario_id"] = tecnico_asignado_usuario_id
    if tecnico_nombre is not None:
        extra["tecnico_nombre"] = tecnico_nombre
    return await _aplicar_transicion(client_id, orden_trabajo_id, "programar", extra)


async def iniciar_orden_trabajo(
    client_id: UUID,
    orden_trabajo_id: UUID,
    fecha_inicio_real: Optional[datetime] = None,
) -> OrdenTrabajoRead:
    """`programada` -> `en_proceso`. Setea `fecha_inicio_real` (default = ahora)."""
    extra = {"fecha_inicio_real": fecha_inicio_real or datetime.utcnow()}
    return await _aplicar_transicion(client_id, orden_trabajo_id, "iniciar", extra)


async def pausar_orden_trabajo(client_id: UUID, orden_trabajo_id: UUID) -> OrdenTrabajoRead:
    """`en_proceso` -> `pausada`."""
    return await _aplicar_transicion(client_id, orden_trabajo_id, "pausar")


async def reanudar_orden_trabajo(client_id: UUID, orden_trabajo_id: UUID) -> OrdenTrabajoRead:
    """`pausada` -> `en_proceso`."""
    return await _aplicar_transicion(client_id, orden_trabajo_id, "reanudar")


async def completar_orden_trabajo(
    client_id: UUID,
    orden_trabajo_id: UUID,
    fecha_fin_real: Optional[datetime] = None,
    trabajo_realizado: Optional[str] = None,
    repuestos_utilizados: Optional[str] = None,
    costo_mano_obra: Optional[Decimal] = None,
    costo_repuestos: Optional[Decimal] = None,
    costo_servicios_terceros: Optional[Decimal] = None,
) -> OrdenTrabajoRead:
    """`en_proceso` -> `completada`. Setea `fecha_fin_real` y opcionalmente costos/trabajo."""
    extra: Dict[str, Any] = {"fecha_fin_real": fecha_fin_real or datetime.utcnow()}
    if trabajo_realizado is not None:
        extra["trabajo_realizado"] = trabajo_realizado
    if repuestos_utilizados is not None:
        extra["repuestos_utilizados"] = repuestos_utilizados
    if costo_mano_obra is not None:
        extra["costo_mano_obra"] = costo_mano_obra
    if costo_repuestos is not None:
        extra["costo_repuestos"] = costo_repuestos
    if costo_servicios_terceros is not None:
        extra["costo_servicios_terceros"] = costo_servicios_terceros
    return await _aplicar_transicion(client_id, orden_trabajo_id, "completar", extra)


async def cancelar_orden_trabajo(
    client_id: UUID,
    orden_trabajo_id: UUID,
    observaciones: Optional[str] = None,
) -> OrdenTrabajoRead:
    """Cualquier estado salvo `cerrada` o `cancelada` -> `cancelada`."""
    current = await _get(client_id, orden_trabajo_id)
    if not current:
        raise NotFoundError(f"Orden de trabajo {orden_trabajo_id} no encontrada")
    estado_actual = _normaliza_estado(current.get("estado"))
    if estado_actual in _ESTADOS_NO_CANCELABLES:
        raise ConflictError(
            detail=(
                f"No se puede cancelar una OT en estado '{estado_actual}'. "
                f"Los estados terminales no son cancelables."
            ),
            internal_code="MNT_OT_TRANSITION_INVALID_CANCELAR",
        )
    payload: Dict[str, Any] = {"estado": ESTADO_CANCELADA}
    if observaciones is not None:
        payload["observaciones"] = observaciones
    row = await _update(client_id, orden_trabajo_id, payload)
    if not row:
        raise NotFoundError(f"Orden de trabajo {orden_trabajo_id} no encontrada")
    return OrdenTrabajoRead(**_enrich_ot(row))


# --------------------------------------------------------------------------
# Cierre transaccional (completada -> cerrada)
# --------------------------------------------------------------------------
def _calcular_proxima_fecha_plan(
    plan: Dict[str, Any], fecha_base: date
) -> Optional[date]:
    """Calcula la siguiente fecha de mantenimiento solo cuando frecuencia_tipo='dias'.

    Para otros tipos (horas_uso, kilometros, ciclos) no es posible calcular
    desde una fecha aislada; se deja en None y el integrador puede actualizar
    `horas_uso_proximo` por separado.
    """
    frecuencia_tipo = (plan.get("frecuencia_tipo") or "").strip().lower()
    frecuencia_valor = plan.get("frecuencia_valor")
    if frecuencia_tipo == "dias" and isinstance(frecuencia_valor, int) and frecuencia_valor > 0:
        return fecha_base + timedelta(days=frecuencia_valor)
    return None


async def cerrar_orden_trabajo(
    client_id: UUID,
    orden_trabajo_id: UUID,
    cerrado_por_usuario_id: Optional[UUID] = None,
    calificacion_trabajo: Optional[Decimal] = None,
    observaciones_historial: Optional[str] = None,
) -> OrdenTrabajoRead:
    """`completada` -> `cerrada` (transaccional).

    Operaciones dentro del mismo UnitOfWork (BEGIN / COMMIT / ROLLBACK):
        1. UPDATE mnt_orden_trabajo:
           - estado='cerrada', fecha_cierre=now,
             cerrado_por_usuario_id, calificacion_trabajo
        2. INSERT mnt_historial_mantenimiento (bitácora derivada)
        3. UPDATE mnt_plan_mantenimiento (si plan_mantenimiento_id no es nulo):
           - fecha_ultimo_mantenimiento, fecha_proximo_mantenimiento
    """
    if calificacion_trabajo is not None:
        if calificacion_trabajo < Decimal("1") or calificacion_trabajo > Decimal("5"):
            raise ConflictError(
                detail="calificacion_trabajo debe estar entre 1.00 y 5.00.",
                internal_code="MNT_OT_CALIFICACION_INVALIDA",
            )

    now = datetime.utcnow()
    today = now.date()

    async with unit_of_work(client_id=client_id) as uow:
        # 1) Leer y validar OT
        ot_rows = await uow.execute(
            select(MntOrdenTrabajoTable).where(
                and_(
                    MntOrdenTrabajoTable.c.cliente_id == client_id,
                    MntOrdenTrabajoTable.c.orden_trabajo_id == orden_trabajo_id,
                )
            )
        )
        ot = ot_rows[0] if ot_rows else None
        if not ot:
            raise NotFoundError(f"Orden de trabajo {orden_trabajo_id} no encontrada")
        estado_actual = _normaliza_estado(ot.get("estado"))
        if estado_actual != "completada":
            raise ConflictError(
                detail=(
                    f"No se puede cerrar una OT en estado '{estado_actual}'. "
                    f"Solo se cierran OT en estado 'completada'."
                ),
                internal_code="MNT_OT_TRANSITION_INVALID_CERRAR",
            )

        empresa_id = ot.get("empresa_id")
        activo_id = ot.get("activo_id")
        plan_mantenimiento_id = ot.get("plan_mantenimiento_id")

        # 2) UPDATE cabecera de OT
        ot_update_values: Dict[str, Any] = {
            "estado": ESTADO_FINAL_CERRADA,
            "fecha_cierre": now,
        }
        if cerrado_por_usuario_id is not None:
            ot_update_values["cerrado_por_usuario_id"] = cerrado_por_usuario_id
        if calificacion_trabajo is not None:
            ot_update_values["calificacion_trabajo"] = calificacion_trabajo

        await uow.execute(
            update(MntOrdenTrabajoTable)
            .where(
                and_(
                    MntOrdenTrabajoTable.c.cliente_id == client_id,
                    MntOrdenTrabajoTable.c.orden_trabajo_id == orden_trabajo_id,
                )
            )
            .values(**ot_update_values)
        )

        # 3) INSERT en mnt_historial_mantenimiento (bitácora derivada)
        costo_total = (
            (ot.get("costo_mano_obra") or Decimal("0"))
            + (ot.get("costo_repuestos") or Decimal("0"))
            + (ot.get("costo_servicios_terceros") or Decimal("0"))
        )
        descripcion_trabajo = ot.get("trabajo_realizado") or ot.get("trabajo_a_realizar")
        observaciones_final = (
            observaciones_historial
            if observaciones_historial is not None
            else ot.get("observaciones")
        )
        fecha_mantenimiento = (
            ot.get("fecha_fin_real").date()
            if isinstance(ot.get("fecha_fin_real"), datetime)
            else today
        )

        historial_values = {
            "historial_id": uuid.uuid4(),
            "cliente_id": client_id,
            "empresa_id": empresa_id,
            "activo_id": activo_id,
            "orden_trabajo_id": orden_trabajo_id,
            "fecha_mantenimiento": fecha_mantenimiento,
            "tipo_mantenimiento": ot.get("tipo_mantenimiento"),
            "descripcion_trabajo": descripcion_trabajo,
            "tecnico_nombre": ot.get("tecnico_nombre"),
            "horas_uso_activo": None,
            "kilometraje": None,
            "costo_total": costo_total,
            "moneda": ot.get("moneda"),
            "observaciones": observaciones_final,
        }
        # Filtrar a columnas reales de la tabla (compatibilidad con mapeo SQLAlchemy actual)
        historial_cols = {c.name for c in MntHistorialMantenimientoTable.c}
        historial_payload = {
            k: v for k, v in historial_values.items() if k in historial_cols
        }
        await uow.execute(insert(MntHistorialMantenimientoTable).values(**historial_payload))

        # 4) UPDATE en mnt_plan_mantenimiento (si plan_mantenimiento_id no es nulo)
        if plan_mantenimiento_id:
            plan_rows = await uow.execute(
                select(MntPlanMantenimientoTable).where(
                    and_(
                        MntPlanMantenimientoTable.c.cliente_id == client_id,
                        MntPlanMantenimientoTable.c.plan_mantenimiento_id
                        == plan_mantenimiento_id,
                    )
                )
            )
            plan = plan_rows[0] if plan_rows else None
            if plan:
                proxima_fecha = _calcular_proxima_fecha_plan(plan, fecha_mantenimiento)
                plan_update_values: Dict[str, Any] = {
                    "fecha_ultimo_mantenimiento": fecha_mantenimiento,
                }
                if proxima_fecha is not None:
                    plan_update_values["fecha_proximo_mantenimiento"] = proxima_fecha
                await uow.execute(
                    update(MntPlanMantenimientoTable)
                    .where(
                        and_(
                            MntPlanMantenimientoTable.c.cliente_id == client_id,
                            MntPlanMantenimientoTable.c.plan_mantenimiento_id
                            == plan_mantenimiento_id,
                        )
                    )
                    .values(**plan_update_values)
                )

        # 5) Releer OT actualizada para la respuesta (dentro de la misma TX)
        ot_final_rows = await uow.execute(
            select(MntOrdenTrabajoTable).where(
                and_(
                    MntOrdenTrabajoTable.c.cliente_id == client_id,
                    MntOrdenTrabajoTable.c.orden_trabajo_id == orden_trabajo_id,
                )
            )
        )
        ot_final = ot_final_rows[0] if ot_final_rows else ot

    # commit hecho al salir de unit_of_work sin excepción
    return OrdenTrabajoRead(**_enrich_ot(ot_final))
