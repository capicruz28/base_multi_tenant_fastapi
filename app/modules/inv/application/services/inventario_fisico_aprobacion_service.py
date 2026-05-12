"""
Servicio de aprobación de Inventario Físico (INV).

Flujo:
- Valida cabecera inventario_fisico y estado.
- Valida tipo_movimiento_id (clase ajuste).
- Lee detalle inventario_fisico_detalle y calcula diferencias.
- Genera un movimiento de ajuste (inv_movimiento) + detalle (inv_movimiento_detalle).
- Procesa el movimiento (actualiza stock) usando el servicio existente.
- Cierra inventario físico (estado ajustado, movimiento_ajuste_id, totales).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID
from datetime import datetime, date

from fastapi import HTTPException, status

from app.core.exceptions import NotFoundError
import uuid
from sqlalchemy import select, insert, update, and_
from app.core.application.unit_of_work import unit_of_work
from app.infrastructure.database.tables_erp import (
    InvInventarioFisicoTable,
    InvInventarioFisicoDetalleTable,
    InvTipoMovimientoTable,
    InvMovimientoTable,
    InvMovimientoDetalleTable,
    InvProductoTable,
)
from app.infrastructure.database.queries.inv import get_moneda_by_codigo
from app.modules.inv.application.services.movimiento_proceso_service import (
    procesar_movimiento_servicio,
)


def _dec(v: Optional[object]) -> Decimal:
    if v is None:
        return Decimal("0")
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _gen_numero_movimiento(prefix: str = "INV-AJUS") -> str:
    # 20 chars max (schema MovimientoCreate). Mantener compacto.
    # Ej: INV-AJUS-240314-1A2B
    stamp = datetime.utcnow().strftime("%y%m%d")
    micro = datetime.utcnow().strftime("%f")[-4:]
    return f"{prefix}-{stamp}-{micro}"[:20]


async def aprobar_inventario_fisico_servicio(
    client_id: UUID,
    inventario_fisico_id: UUID,
    tipo_movimiento_id: UUID,
    usuario_id: Optional[UUID] = None,
    observaciones: Optional[str] = None,
) -> dict:
    # Moneda: alinear a BD (inv_movimiento.moneda_id NOT NULL)
    moneda_row = await get_moneda_by_codigo(client_id=client_id, codigo="PEN", solo_activos=True)
    if not moneda_row:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se pudo resolver moneda_id (cat_moneda) para ajuste",
        )
    moneda_id = moneda_row["moneda_id"]

    async with unit_of_work(client_id=client_id) as uow:
        inv_rows = await uow.execute(
            select(InvInventarioFisicoTable).where(
                and_(
                    InvInventarioFisicoTable.c.cliente_id == client_id,
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
        if estado not in ("en_proceso", "finalizado"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"No se puede aprobar inventario físico en estado '{inv.get('estado')}'",
            )

        tm_rows = await uow.execute(
            select(InvTipoMovimientoTable).where(
                and_(
                    InvTipoMovimientoTable.c.cliente_id == client_id,
                    InvTipoMovimientoTable.c.tipo_movimiento_id == tipo_movimiento_id,
                )
            )
        )
        tm = tm_rows[0] if tm_rows else None
        if not tm:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="tipo_movimiento_id inválido o no pertenece al tenant",
            )
        if (tm.get("clase_movimiento") or "").lower() != "ajuste":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="tipo_movimiento_id debe ser de clase 'ajuste'",
            )

        empresa_id = inv.get("empresa_id")
        almacen_id = inv.get("almacen_id")
        fecha_inventario: Optional[date] = inv.get("fecha_inventario")
        if not empresa_id or not almacen_id or not fecha_inventario:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Inventario físico incompleto (empresa_id/almacen_id/fecha_inventario requeridos)",
            )

        detalles = await uow.execute(
            select(InvInventarioFisicoDetalleTable)
            .where(
                and_(
                    InvInventarioFisicoDetalleTable.c.cliente_id == client_id,
                    InvInventarioFisicoDetalleTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
            .order_by(
                InvInventarioFisicoDetalleTable.c.inventario_fisico_id,
                InvInventarioFisicoDetalleTable.c.fecha_creacion,
            )
        )
        if not detalles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se puede aprobar inventario físico sin detalle",
            )

        # Construir movimiento de ajuste (cabecera)
        numero_movimiento = _gen_numero_movimiento()
        movimiento_id = uuid.uuid4()
        now = datetime.utcnow()
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
                moneda="PEN",
                estado="borrador",
                observaciones=observaciones,
                usuario_creacion_id=usuario_id,
                fecha_actualizacion=now,
            )
        )

        # Crear líneas: diferencia = contada - sistema (puede ser negativa)
        total_items = 0
        total_cantidad_abs = Decimal("0")
        total_productos_contados = 0
        for det in detalles:
            producto_id = det.get("producto_id")
            if not producto_id:
                continue
            sistema = _dec(det.get("cantidad_sistema"))
            contada = det.get("cantidad_contada")
            if contada is None:
                continue
            total_productos_contados += 1
            diferencia = _dec(contada) - sistema
            if diferencia == 0:
                continue

            prod_rows = await uow.execute(
                select(InvProductoTable).where(
                    and_(
                        InvProductoTable.c.cliente_id == client_id,
                        InvProductoTable.c.producto_id == producto_id,
                    )
                )
            )
            prod = prod_rows[0] if prod_rows else None
            if not prod:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Producto inválido en detalle de inventario físico",
                )
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
                    moneda="PEN",
                    lote=det.get("lote"),
                    fecha_vencimiento=det.get("fecha_vencimiento"),
                    numero_serie=None,
                    ubicacion_almacen=det.get("ubicacion_almacen"),
                    observaciones=det.get("observaciones"),
                    fecha_actualizacion=now,
                )
            )
            total_items += 1
            total_cantidad_abs += abs(diferencia)

        if total_items == 0:
            await uow.execute(
                update(InvInventarioFisicoTable)
                .where(
                    and_(
                        InvInventarioFisicoTable.c.cliente_id == client_id,
                        InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                    )
                )
                .values(
                    estado="finalizado",
                    total_productos_contados=total_productos_contados,
                    total_diferencias=0,
                    valor_diferencias=Decimal("0"),
                    fecha_finalizacion=now,
                    fecha_actualizacion=now,
                )
            )
            closed_rows = await uow.execute(
                select(InvInventarioFisicoTable).where(
                    and_(
                        InvInventarioFisicoTable.c.cliente_id == client_id,
                        InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                    )
                )
            )
            return closed_rows[0] if closed_rows else inv

        # Actualizar totales del inventario físico (cabecera)
        await uow.execute(
            update(InvInventarioFisicoTable)
            .where(
                and_(
                    InvInventarioFisicoTable.c.cliente_id == client_id,
                    InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
            .values(
                total_productos_contados=total_productos_contados,
                total_diferencias=total_items,
                fecha_actualizacion=now,
            )
        )

        # Actualizar totales del movimiento (cabecera) antes de procesar
        await uow.execute(
            update(InvMovimientoTable)
            .where(
                and_(
                    InvMovimientoTable.c.cliente_id == client_id,
                    InvMovimientoTable.c.movimiento_id == movimiento_id,
                )
            )
            .values(
                total_items=total_items,
                total_cantidad=total_cantidad_abs,
                fecha_actualizacion=now,
            )
        )

        # Procesar movimiento dentro de la misma transacción
        await procesar_movimiento_servicio(
            client_id=client_id,
            movimiento_id=movimiento_id,
            usuario_procesado_id=usuario_id,
            uow=uow,
        )

        # Cerrar inventario físico
        await uow.execute(
            update(InvInventarioFisicoTable)
            .where(
                and_(
                    InvInventarioFisicoTable.c.cliente_id == client_id,
                    InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
            .values(
                estado="ajustado",
                movimiento_ajuste_id=movimiento_id,
                fecha_ajuste=now,
                fecha_finalizacion=now,
                fecha_actualizacion=now,
            )
        )

        closed_rows = await uow.execute(
            select(InvInventarioFisicoTable).where(
                and_(
                    InvInventarioFisicoTable.c.cliente_id == client_id,
                    InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
        )
        return closed_rows[0] if closed_rows else inv

