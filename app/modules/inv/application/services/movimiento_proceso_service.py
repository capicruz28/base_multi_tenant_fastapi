"""
Servicios de proceso para Movimientos (INV):
- Procesar movimiento: aplica impacto en stock basado en tipo/clase y detalle.
- Anular movimiento: marca anulado (sin reversión automática por ahora).

Diseño conservador:
- No asume transacciones distribuidas; intenta aplicar cambios de forma segura.
- Exige que el movimiento tenga detalle para poder procesarlo.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.inv import (
    get_movimiento_by_id,
    update_movimiento,
    list_movimientos_detalle,
    get_tipo_movimiento_by_id,
    get_stock_by_producto_almacen,
    create_stock,
    update_stock,
)


def _to_decimal(value: Optional[object], default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


async def procesar_movimiento_servicio(
    client_id: UUID,
    movimiento_id: UUID,
    usuario_procesado_id: Optional[UUID] = None,
) -> dict:
    """
    Procesa un movimiento:
    - Valida existencia y estado.
    - Determina clase del tipo de movimiento.
    - Aplica detalle contra inv_stock:
        entrada: +cantidad_base en almacen_destino
        salida:  -cantidad_base en almacen_origen
        transferencia: -origen +destino
        ajuste: si hay origen -> aplica en origen; si hay destino -> aplica en destino
    - Marca movimiento.estado = 'procesado' y fecha_procesado.
    """
    mov = await get_movimiento_by_id(client_id=client_id, movimiento_id=movimiento_id)
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

    tipo_movimiento_id = mov.get("tipo_movimiento_id")
    if not tipo_movimiento_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Movimiento sin tipo_movimiento_id",
        )

    tm = await get_tipo_movimiento_by_id(
        client_id=client_id, tipo_movimiento_id=tipo_movimiento_id
    )
    if not tm:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tipo de movimiento inválido o no pertenece al tenant",
        )

    clase = (tm.get("clase_movimiento") or "").lower()
    almacen_origen_id = mov.get("almacen_origen_id")
    almacen_destino_id = mov.get("almacen_destino_id")
    empresa_id = mov.get("empresa_id")
    if not empresa_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Movimiento sin empresa_id",
        )

    detalles = await list_movimientos_detalle(
        client_id=client_id, movimiento_id=movimiento_id
    )
    if not detalles:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede procesar un movimiento sin detalle",
        )

    async def _apply_delta(almacen_id: UUID, producto_id: UUID, delta: Decimal):
        existing = await get_stock_by_producto_almacen(
            client_id=client_id, producto_id=producto_id, almacen_id=almacen_id
        )
        now = datetime.utcnow()
        if not existing:
            # Crear stock base con cantidad_actual = delta si delta >= 0
            if delta < 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Stock insuficiente (no existe registro de stock para salida)",
                )
            await create_stock(
                client_id=client_id,
                data={
                    "empresa_id": empresa_id,
                    "producto_id": producto_id,
                    "almacen_id": almacen_id,
                    "cantidad_actual": delta,
                    "cantidad_reservada": Decimal("0"),
                    "cantidad_transito": Decimal("0"),
                    "costo_promedio": Decimal("0"),
                    "moneda": "PEN",
                    "fecha_ultimo_movimiento": now,
                },
            )
            return
        current = _to_decimal(existing.get("cantidad_actual"), "0")
        new_value = current + delta
        if new_value < 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stock insuficiente para procesar el movimiento",
            )
        await update_stock(
            client_id=client_id,
            stock_id=existing["stock_id"],
            data={
                "cantidad_actual": new_value,
                "fecha_ultimo_movimiento": now,
            },
        )

    # Aplicar según clase
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
            # Ajuste: aplica contra el almacén definido (prioriza destino si existe)
            target_almacen = almacen_destino_id or almacen_origen_id
            if not target_almacen:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Ajuste requiere almacen_origen_id o almacen_destino_id",
                )
            # Para ajuste, qty se interpreta como cantidad_base con signo según se quiera:
            # si qty es positiva, entrada; si negativa, salida.
            await _apply_delta(target_almacen, producto_id, qty)
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Clase de movimiento no soportada: {clase}",
            )

    # Marcar procesado
    updated = await update_movimiento(
        client_id=client_id,
        movimiento_id=movimiento_id,
        data={
            "estado": "procesado",
            "fecha_procesado": datetime.utcnow(),
            "usuario_procesado_id": usuario_procesado_id,
        },
    )
    return updated


async def anular_movimiento_servicio(
    client_id: UUID,
    movimiento_id: UUID,
    motivo: Optional[str] = None,
) -> dict:
    """
    Marca un movimiento como anulado.
    Nota: no revierte stock automáticamente para evitar inconsistencias.
    """
    mov = await get_movimiento_by_id(client_id=client_id, movimiento_id=movimiento_id)
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
    )
    return updated

