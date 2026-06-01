"""
Servicios de proceso para Movimientos (INV):
- Procesar movimiento: aplica impacto en stock basado en tipo/clase y detalle.
- Autorizar / anular movimiento.

Aislamiento multi-empresa: empresa_id desde sesión JWT (company_scope).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID
from datetime import datetime
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, insert, update, and_

from app.core.exceptions import NotFoundError
from app.core.application.unit_of_work import unit_of_work, UnitOfWork
from app.core.tenant.company_scope import require_session_empresa_id
from app.infrastructure.database.tables_erp import (
    InvMovimientoTable,
    InvMovimientoDetalleTable,
    InvTipoMovimientoTable,
    InvStockTable,
)
from app.infrastructure.database.queries.inv import (
    get_moneda_by_codigo,
    get_movimiento_by_id,
    update_movimiento,
    get_almacen_by_id,
    get_producto_by_id,
)


def _to_decimal(value: Optional[object], default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


async def _validate_proceso_referencias(
    client_id: UUID,
    empresa_id: UUID,
    mov: dict,
    detalles: list[dict],
) -> None:
    """Almacenes y productos del movimiento deben pertenecer a la empresa de sesión."""
    for alm_id, label in (
        (mov.get("almacen_origen_id"), "Almacén origen"),
        (mov.get("almacen_destino_id"), "Almacén destino"),
    ):
        if alm_id is not None:
            alm = await get_almacen_by_id(
                client_id=client_id,
                almacen_id=alm_id,
                empresa_id=empresa_id,
            )
            if not alm:
                raise NotFoundError(detail=f"{label} no encontrado")

    for det in detalles:
        producto_id = det.get("producto_id")
        if not producto_id:
            continue
        prod = await get_producto_by_id(
            client_id=client_id,
            producto_id=producto_id,
            empresa_id=empresa_id,
        )
        if not prod:
            raise NotFoundError(detail="Producto no encontrado")


async def procesar_movimiento_servicio(
    client_id: UUID,
    movimiento_id: UUID,
    usuario_procesado_id: Optional[UUID] = None,
    uow: Optional[UnitOfWork] = None,
) -> dict:
    """
    Procesa un movimiento de la empresa activa en sesión.
    Cross-company → NotFoundError; no muta stock de otra empresa.
    """
    empresa_id = require_session_empresa_id()

    async def _run(uow_run: UnitOfWork) -> dict:
        rows = await uow_run.execute(
            select(InvMovimientoTable).where(
                and_(
                    InvMovimientoTable.c.cliente_id == client_id,
                    InvMovimientoTable.c.empresa_id == empresa_id,
                    InvMovimientoTable.c.movimiento_id == movimiento_id,
                )
            )
        )
        mov = rows[0] if rows else None
        if not mov:
            raise NotFoundError(detail="Movimiento no encontrado")

        estado = (mov.get("estado") or "").lower()
        if estado == "procesado":
            return mov
        if estado == "anulado":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede procesar un movimiento anulado",
            )
        if bool(mov.get("requiere_autorizacion")) and estado != "autorizado":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Movimiento requiere autorización previa (estado debe ser 'autorizado')",
            )

        tipo_movimiento_id = mov.get("tipo_movimiento_id")
        if not tipo_movimiento_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Movimiento sin tipo_movimiento_id",
            )

        tm_rows = await uow_run.execute(
            select(InvTipoMovimientoTable).where(
                and_(
                    InvTipoMovimientoTable.c.cliente_id == client_id,
                    InvTipoMovimientoTable.c.empresa_id == empresa_id,
                    InvTipoMovimientoTable.c.tipo_movimiento_id == tipo_movimiento_id,
                )
            )
        )
        tm = tm_rows[0] if tm_rows else None
        if not tm:
            raise NotFoundError(detail="Tipo de movimiento no encontrado")

        clase = (tm.get("clase_movimiento") or "").lower()
        almacen_origen_id = mov.get("almacen_origen_id")
        almacen_destino_id = mov.get("almacen_destino_id")
        moneda_id = mov.get("moneda_id")
        if not moneda_id:
            moneda_row = await get_moneda_by_codigo(
                client_id=client_id, codigo="PEN", solo_activos=True
            )
            if not moneda_row:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="No se puede resolver moneda_id (cat_moneda) para el movimiento",
                )
            moneda_id = moneda_row["moneda_id"]

        detalles = await uow_run.execute(
            select(InvMovimientoDetalleTable)
            .where(
                and_(
                    InvMovimientoDetalleTable.c.cliente_id == client_id,
                    InvMovimientoDetalleTable.c.empresa_id == empresa_id,
                    InvMovimientoDetalleTable.c.movimiento_id == movimiento_id,
                )
            )
            .order_by(InvMovimientoDetalleTable.c.fecha_creacion)
        )
        if not detalles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se puede procesar un movimiento sin detalle",
            )

        await _validate_proceso_referencias(client_id, empresa_id, mov, detalles)

        async def _apply_delta(almacen_id: UUID, producto_id: UUID, delta: Decimal):
            existing_rows = await uow_run.execute(
                select(InvStockTable).where(
                    and_(
                        InvStockTable.c.cliente_id == client_id,
                        InvStockTable.c.empresa_id == empresa_id,
                        InvStockTable.c.producto_id == producto_id,
                        InvStockTable.c.almacen_id == almacen_id,
                    )
                )
            )
            existing = existing_rows[0] if existing_rows else None
            now = datetime.utcnow()
            if not existing:
                if delta < 0:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Stock insuficiente (no existe registro de stock para salida)",
                    )
                await uow_run.execute(
                    insert(InvStockTable).values(
                        stock_id=uuid.uuid4(),
                        cliente_id=client_id,
                        empresa_id=empresa_id,
                        producto_id=producto_id,
                        almacen_id=almacen_id,
                        cantidad_actual=delta,
                        cantidad_reservada=Decimal("0"),
                        cantidad_transito=Decimal("0"),
                        costo_promedio=Decimal("0"),
                        moneda_id=moneda_id,
                        fecha_ultimo_movimiento=now,
                        fecha_actualizacion=now,
                    )
                )
                return

            current = _to_decimal(existing.get("cantidad_actual"), "0")
            new_value = current + delta
            if new_value < 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Stock insuficiente para procesar el movimiento",
                )
            await uow_run.execute(
                update(InvStockTable)
                .where(
                    and_(
                        InvStockTable.c.cliente_id == client_id,
                        InvStockTable.c.empresa_id == empresa_id,
                        InvStockTable.c.stock_id == existing["stock_id"],
                    )
                )
                .values(
                    cantidad_actual=new_value,
                    fecha_ultimo_movimiento=now,
                    fecha_actualizacion=now,
                )
            )

        for det in detalles:
            producto_id = det.get("producto_id")
            qty = _to_decimal(det.get("cantidad_base"), "0")
            if not producto_id or qty == 0:
                continue

            if clase == "entrada":
                if not almacen_destino_id:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Movimiento de entrada requiere almacen_destino_id",
                    )
                await _apply_delta(almacen_destino_id, producto_id, qty)
            elif clase == "salida":
                if not almacen_origen_id:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Movimiento de salida requiere almacen_origen_id",
                    )
                await _apply_delta(almacen_origen_id, producto_id, -qty)
            elif clase == "transferencia":
                if not almacen_origen_id or not almacen_destino_id:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Transferencia requiere almacen_origen_id y almacen_destino_id",
                    )
                await _apply_delta(almacen_origen_id, producto_id, -qty)
                await _apply_delta(almacen_destino_id, producto_id, qty)
            elif clase == "ajuste":
                target_almacen = almacen_destino_id or almacen_origen_id
                if not target_almacen:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Ajuste requiere almacen_origen_id o almacen_destino_id",
                    )
                await _apply_delta(target_almacen, producto_id, qty)
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Clase de movimiento no soportada: {clase}",
                )

        await uow_run.execute(
            update(InvMovimientoTable)
            .where(
                and_(
                    InvMovimientoTable.c.cliente_id == client_id,
                    InvMovimientoTable.c.empresa_id == empresa_id,
                    InvMovimientoTable.c.movimiento_id == movimiento_id,
                )
            )
            .values(
                estado="procesado",
                fecha_procesado=datetime.utcnow(),
                usuario_procesado_id=usuario_procesado_id,
                fecha_actualizacion=datetime.utcnow(),
            )
        )

        updated_rows = await uow_run.execute(
            select(InvMovimientoTable).where(
                and_(
                    InvMovimientoTable.c.cliente_id == client_id,
                    InvMovimientoTable.c.empresa_id == empresa_id,
                    InvMovimientoTable.c.movimiento_id == movimiento_id,
                )
            )
        )
        return updated_rows[0] if updated_rows else mov

    if uow is not None:
        return await _run(uow)

    async with unit_of_work(client_id=client_id) as uow2:
        return await _run(uow2)


async def autorizar_movimiento_servicio(
    *,
    client_id: UUID,
    movimiento_id: UUID,
    usuario_autorizado_id: Optional[UUID] = None,
) -> dict:
    """Autoriza un movimiento de la empresa activa en sesión."""
    empresa_id = require_session_empresa_id()
    mov = await get_movimiento_by_id(
        client_id=client_id,
        movimiento_id=movimiento_id,
        empresa_id=empresa_id,
    )
    if not mov:
        raise NotFoundError(detail="Movimiento no encontrado")

    estado = (mov.get("estado") or "").lower()
    if estado == "autorizado":
        return mov
    if estado in ("procesado", "anulado"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede autorizar un movimiento en estado '{mov.get('estado')}'",
        )

    updated = await update_movimiento(
        client_id=client_id,
        movimiento_id=movimiento_id,
        data={
            "estado": "autorizado",
            "autorizado_por_usuario_id": usuario_autorizado_id,
            "fecha_autorizacion": datetime.utcnow(),
        },
        empresa_id=empresa_id,
    )
    return updated


async def anular_movimiento_servicio(
    client_id: UUID,
    movimiento_id: UUID,
    motivo: Optional[str] = None,
) -> dict:
    """Anula un movimiento de la empresa activa en sesión (sin reversión de stock)."""
    empresa_id = require_session_empresa_id()
    mov = await get_movimiento_by_id(
        client_id=client_id,
        movimiento_id=movimiento_id,
        empresa_id=empresa_id,
    )
    if not mov:
        raise NotFoundError(detail="Movimiento no encontrado")

    estado = (mov.get("estado") or "").lower()
    if estado == "anulado":
        return mov
    if estado == "procesado":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede anular un movimiento procesado sin reversión explícita",
        )

    updated = await update_movimiento(
        client_id=client_id,
        movimiento_id=movimiento_id,
        data={
            "estado": "anulado",
            "motivo_anulacion": motivo,
            "fecha_actualizacion": datetime.utcnow(),
        },
        empresa_id=empresa_id,
    )
    return updated
