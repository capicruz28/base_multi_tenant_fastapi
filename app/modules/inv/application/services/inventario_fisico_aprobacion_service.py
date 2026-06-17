"""
Servicio de aprobación de Inventario Físico (INV).

Aislamiento multi-empresa: empresa_id desde sesión JWT (company_scope).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID
from datetime import datetime, date

from fastapi import HTTPException, status

from app.core.exceptions import NotFoundError
import uuid
from sqlalchemy import select, insert, update, and_
from app.core.application.unit_of_work import unit_of_work
from app.core.tenant.company_scope import require_session_empresa_id
from app.infrastructure.database.tables_erp import (
    InvInventarioFisicoTable,
    InvInventarioFisicoDetalleTable,
    InvMovimientoTable,
    InvMovimientoDetalleTable,
)
from app.infrastructure.database.queries.inv import (
    get_moneda_by_codigo,
    get_tipo_movimiento_by_id,
    get_producto_by_id,
    get_almacen_by_id,
)
from app.modules.inv.application.services.movimiento_proceso_service import (
    procesar_movimiento_servicio,
)

_MSG_APROBAR_REQUIERE_FINALIZADO = (
    "Debe finalizar el conteo antes de aprobar el ajuste de inventario."
)
_MSG_APROBAR_SIN_DIFERENCIAS = (
    "No existen diferencias de inventario para aprobar. "
    "Utilice POST /inventario-fisico/{id}/finalizar para cerrar el conteo sin ajuste de stock."
)


def _dec(v: Optional[object]) -> Decimal:
    if v is None:
        return Decimal("0")
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _gen_numero_movimiento(prefix: str = "INV-AJUS") -> str:
    stamp = datetime.utcnow().strftime("%y%m%d")
    micro = datetime.utcnow().strftime("%f")[-4:]
    return f"{prefix}-{stamp}-{micro}"[:20]


@dataclass(frozen=True)
class _LineaAjusteInventarioFisico:
    det: dict
    producto_id: UUID
    diferencia: Decimal


def _clasificar_lineas_aprobacion(
    detalles: list[dict],
) -> tuple[int, int, Decimal, list[_LineaAjusteInventarioFisico]]:
    """
    Clasifica el detalle del inventario físico en un solo recorrido.

    Retorna:
        total_productos_contados, total_items, total_cantidad_abs, lineas_ajuste
    """
    total_productos_contados = 0
    total_items = 0
    total_cantidad_abs = Decimal("0")
    lineas_ajuste: list[_LineaAjusteInventarioFisico] = []

    for det in detalles:
        producto_id = det.get("producto_id")
        if not producto_id:
            continue
        contada = det.get("cantidad_contada")
        if contada is None:
            continue
        total_productos_contados += 1
        diferencia = _dec(contada) - _dec(det.get("cantidad_sistema"))
        if diferencia == 0:
            continue
        lineas_ajuste.append(
            _LineaAjusteInventarioFisico(
                det=det,
                producto_id=producto_id,
                diferencia=diferencia,
            )
        )
        total_items += 1
        total_cantidad_abs += abs(diferencia)

    return total_productos_contados, total_items, total_cantidad_abs, lineas_ajuste


async def aprobar_inventario_fisico_servicio(
    client_id: UUID,
    inventario_fisico_id: UUID,
    tipo_movimiento_id: UUID,
    usuario_id: Optional[UUID] = None,
    observaciones: Optional[str] = None,
) -> dict:
    empresa_id = require_session_empresa_id()

    moneda_row = await get_moneda_by_codigo(client_id=client_id, codigo="PEN", solo_activos=True)
    if not moneda_row:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se pudo resolver moneda_id (cat_moneda) para ajuste",
        )
    moneda_id = moneda_row["moneda_id"]

    tm = await get_tipo_movimiento_by_id(
        client_id=client_id,
        tipo_movimiento_id=tipo_movimiento_id,
        empresa_id=empresa_id,
    )
    if not tm:
        raise NotFoundError(detail="Tipo de movimiento no encontrado")
    if (tm.get("clase_movimiento") or "").lower() != "ajuste":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="tipo_movimiento_id debe ser de clase 'ajuste'",
        )

    async with unit_of_work(client_id=client_id) as uow:
        inv_rows = await uow.execute(
            select(InvInventarioFisicoTable).where(
                and_(
                    InvInventarioFisicoTable.c.cliente_id == client_id,
                    InvInventarioFisicoTable.c.empresa_id == empresa_id,
                    InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
        )
        inv = inv_rows[0] if inv_rows else None
        if not inv:
            raise NotFoundError(detail="Inventario físico no encontrado")

        estado = (inv.get("estado") or "").lower()
        if estado in ("ajustado", "anulado"):
            return inv
        if estado == "en_proceso":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=_MSG_APROBAR_REQUIERE_FINALIZADO,
            )
        if estado != "finalizado":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se puede aprobar inventario físico en estado '{inv.get('estado')}'",
            )

        almacen_id = inv.get("almacen_id")
        fecha_inventario: Optional[date] = inv.get("fecha_inventario")
        if not almacen_id or not fecha_inventario:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Inventario físico incompleto (almacen_id/fecha_inventario requeridos)",
            )

        alm = await get_almacen_by_id(
            client_id=client_id,
            almacen_id=almacen_id,
            empresa_id=empresa_id,
        )
        if not alm:
            raise NotFoundError(detail="Almacén no encontrado")

        detalles = await uow.execute(
            select(InvInventarioFisicoDetalleTable)
            .where(
                and_(
                    InvInventarioFisicoDetalleTable.c.cliente_id == client_id,
                    InvInventarioFisicoDetalleTable.c.empresa_id == empresa_id,
                    InvInventarioFisicoDetalleTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
            .order_by(InvInventarioFisicoDetalleTable.c.fecha_creacion)
        )
        if not detalles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se puede aprobar inventario físico sin detalle",
            )

        now = datetime.utcnow()
        (
            total_productos_contados,
            total_items,
            total_cantidad_abs,
            lineas_ajuste,
        ) = _clasificar_lineas_aprobacion(detalles)

        if total_items == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=_MSG_APROBAR_SIN_DIFERENCIAS,
            )

        numero_movimiento = _gen_numero_movimiento()
        movimiento_id = uuid.uuid4()
        await uow.execute(
            insert(InvMovimientoTable).values(
                movimiento_id=movimiento_id,
                cliente_id=client_id,
                empresa_id=empresa_id,
                numero_movimiento=numero_movimiento,
                tipo_movimiento_id=tipo_movimiento_id,
                fecha_movimiento=now,
                fecha_contable=fecha_inventario,
                almacen_origen_id=None,
                almacen_destino_id=almacen_id,
                modulo_origen="INV",
                documento_referencia_tipo="inventario_fisico",
                documento_referencia_id=inventario_fisico_id,
                documento_referencia_numero=inv.get("numero_inventario"),
                total_items=0,
                total_cantidad=Decimal("0"),
                total_costo=Decimal("0"),
                moneda_id=moneda_id,
                estado="borrador",
                observaciones=observaciones,
                usuario_creacion_id=usuario_id,
                fecha_actualizacion=now,
            )
        )

        for linea in lineas_ajuste:
            det = linea.det
            producto_id = linea.producto_id
            diferencia = linea.diferencia

            prod = await get_producto_by_id(
                client_id=client_id,
                producto_id=producto_id,
                empresa_id=empresa_id,
            )
            if not prod:
                raise NotFoundError(detail="Producto no encontrado")
            unidad_medida_id = prod.get("unidad_medida_base_id")
            if not unidad_medida_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Producto sin unidad_medida_base_id",
                )

            await uow.execute(
                insert(InvMovimientoDetalleTable).values(
                    movimiento_detalle_id=uuid.uuid4(),
                    cliente_id=client_id,
                    empresa_id=empresa_id,
                    movimiento_id=movimiento_id,
                    producto_id=producto_id,
                    cantidad=diferencia,
                    unidad_medida_id=unidad_medida_id,
                    cantidad_base=diferencia,
                    costo_unitario=det.get("costo_unitario") or Decimal("0"),
                    moneda_id=moneda_id,
                    lote=det.get("lote"),
                    fecha_vencimiento=det.get("fecha_vencimiento"),
                    numero_serie=None,
                    ubicacion_almacen=det.get("ubicacion_almacen"),
                    observaciones=det.get("observaciones"),
                )
            )

        await uow.execute(
            update(InvInventarioFisicoTable)
            .where(
                and_(
                    InvInventarioFisicoTable.c.cliente_id == client_id,
                    InvInventarioFisicoTable.c.empresa_id == empresa_id,
                    InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
            .values(
                total_productos_contados=total_productos_contados,
                total_diferencias=total_items,
            )
        )

        await uow.execute(
            update(InvMovimientoTable)
            .where(
                and_(
                    InvMovimientoTable.c.cliente_id == client_id,
                    InvMovimientoTable.c.empresa_id == empresa_id,
                    InvMovimientoTable.c.movimiento_id == movimiento_id,
                )
            )
            .values(
                total_items=total_items,
                total_cantidad=total_cantidad_abs,
                fecha_actualizacion=now,
            )
        )

        await procesar_movimiento_servicio(
            client_id=client_id,
            movimiento_id=movimiento_id,
            usuario_procesado_id=usuario_id,
            uow=uow,
        )

        await uow.execute(
            update(InvInventarioFisicoTable)
            .where(
                and_(
                    InvInventarioFisicoTable.c.cliente_id == client_id,
                    InvInventarioFisicoTable.c.empresa_id == empresa_id,
                    InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
            .values(
                estado="ajustado",
                movimiento_ajuste_id=movimiento_id,
                fecha_ajuste=now,
                fecha_finalizacion=now,
            )
        )

        closed_rows = await uow.execute(
            select(InvInventarioFisicoTable).where(
                and_(
                    InvInventarioFisicoTable.c.cliente_id == client_id,
                    InvInventarioFisicoTable.c.empresa_id == empresa_id,
                    InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
        )
        return closed_rows[0] if closed_rows else inv
