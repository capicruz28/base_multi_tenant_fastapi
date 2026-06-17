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

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.inv.application.services.inv_estorno_proceso import (
    SQL_LOCK_MOVIMIENTO_ORIGINAL,
    assert_compensatorio_no_existe,
    assert_entrada_espejo_ppm_viable,
    assert_estorno_mvp_allowed,
    build_compensatorio_cabecera_espejo,
    build_compensatorio_detalles,
    find_compensatorio_by_original,
    gen_numero_movimiento_estorno,
    ESTORNO_NO_PROCESADO_CODE,
    ESTORNO_UPDATE_RACE_CODE,
    MOVIMIENTO_YA_ESTORNADO_CODE,
)
from app.modules.inv.application.services.inv_workflow_enforcement import (
    assert_movimiento_autorizable,
    assert_movimiento_procesable,
)
from app.modules.inv.application.services.inv_costeo_proceso import (
    apply_if_zero_costo_policy,
    calc_costo_transferencia_destino_propagacion,
    calc_ppm_entrada,
    calc_ppm_transferencia_destino,
    is_movimiento_inventario_fisico,
    round_costo,
    validate_costo_unitario_for_process,
)
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


_MOV_COLUMNS = {c.name for c in InvMovimientoTable.c}
_MOV_DET_COLUMNS = {c.name for c in InvMovimientoDetalleTable.c}


def _to_decimal(value: Optional[object], default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _afecta_costo_from_tipo(tm: dict) -> bool:
    raw = tm.get("afecta_costo")
    if raw is None:
        return True
    return bool(raw)


def _resolve_costo_entrada_line(
    *,
    q: Decimal,
    c: Decimal,
    delta: Decimal,
    cu: Decimal,
    stock_exists: bool,
    afecta_costo: bool,
    es_movimiento_if: bool,
) -> Optional[Decimal]:
    if not afecta_costo:
        return None
    if es_movimiento_if and cu <= 0:
        if stock_exists:
            return apply_if_zero_costo_policy(c)
        return Decimal("0")
    return calc_ppm_entrada(q, c, delta, cu, stock_exists=stock_exists)


def _resolve_costo_transferencia_destino(
    *,
    q_dest: Decimal,
    c_dest: Decimal,
    delta: Decimal,
    cu_eff: Decimal,
    dest_exists: bool,
    afecta_costo: bool,
) -> Optional[Decimal]:
    if not dest_exists:
        return calc_costo_transferencia_destino_propagacion(cu_eff)
    if not afecta_costo:
        return None
    return calc_ppm_transferencia_destino(
        q_dest,
        c_dest,
        delta,
        cu_eff,
        stock_exists=True,
    )


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
            assert_movimiento_procesable(mov)
            return mov
        if estado == "anulado":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede procesar un movimiento anulado",
            )
        if estado == "estornado":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede procesar un movimiento estornado",
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
        afecta_costo = _afecta_costo_from_tipo(tm)
        es_movimiento_if = is_movimiento_inventario_fisico(mov)
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

        async def _fetch_stock(almacen_id: UUID, producto_id: UUID) -> Optional[dict]:
            stock_rows = await uow_run.execute(
                select(InvStockTable).where(
                    and_(
                        InvStockTable.c.cliente_id == client_id,
                        InvStockTable.c.empresa_id == empresa_id,
                        InvStockTable.c.producto_id == producto_id,
                        InvStockTable.c.almacen_id == almacen_id,
                    )
                )
            )
            return stock_rows[0] if stock_rows else None

        async def _apply_delta(
            almacen_id: UUID,
            producto_id: UUID,
            delta: Decimal,
            *,
            costo_promedio_objetivo: Optional[Decimal] = None,
        ) -> None:
            existing = await _fetch_stock(almacen_id, producto_id)
            now = datetime.utcnow()
            if not existing:
                if delta < 0:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Stock insuficiente (no existe registro de stock para salida)",
                    )
                costo_insert = (
                    round_costo(costo_promedio_objetivo)
                    if costo_promedio_objetivo is not None
                    else Decimal("0")
                )
                producto = await get_producto_by_id(
                    client_id=client_id,
                    producto_id=producto_id,
                    empresa_id=empresa_id,
                )
                insert_values = {
                    "stock_id": uuid.uuid4(),
                    "cliente_id": client_id,
                    "empresa_id": empresa_id,
                    "producto_id": producto_id,
                    "almacen_id": almacen_id,
                    "cantidad_actual": delta,
                    "cantidad_reservada": Decimal("0"),
                    "cantidad_transito": Decimal("0"),
                    "costo_promedio": costo_insert,
                    "moneda_id": moneda_id,
                    "fecha_ultimo_movimiento": now,
                    "fecha_actualizacion": now,
                }
                if producto:
                    for field in ("stock_minimo", "stock_maximo", "punto_reorden"):
                        if producto.get(field) is not None:
                            insert_values[field] = producto[field]
                await uow_run.execute(insert(InvStockTable).values(**insert_values))
                return

            current = _to_decimal(existing.get("cantidad_actual"), "0")
            new_value = current + delta
            if new_value < 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Stock insuficiente para procesar el movimiento",
                )
            update_values = {
                "cantidad_actual": new_value,
                "fecha_ultimo_movimiento": now,
                "fecha_actualizacion": now,
            }
            if costo_promedio_objetivo is not None:
                update_values["costo_promedio"] = round_costo(costo_promedio_objetivo)
            await uow_run.execute(
                update(InvStockTable)
                .where(
                    and_(
                        InvStockTable.c.cliente_id == client_id,
                        InvStockTable.c.empresa_id == empresa_id,
                        InvStockTable.c.stock_id == existing["stock_id"],
                    )
                )
                .values(**update_values)
            )

        async def _apply_entrada_o_ajuste_positivo(
            almacen_id: UUID,
            producto_id: UUID,
            qty: Decimal,
            cu: Decimal,
        ) -> None:
            validate_costo_unitario_for_process(
                afecta_costo=afecta_costo,
                costo_unitario=cu,
                es_movimiento_if=es_movimiento_if,
                clase=clase,
                delta=qty,
            )
            existing = await _fetch_stock(almacen_id, producto_id)
            q = _to_decimal(existing.get("cantidad_actual")) if existing else Decimal("0")
            c = _to_decimal(existing.get("costo_promedio")) if existing else Decimal("0")
            costo_obj = _resolve_costo_entrada_line(
                q=q,
                c=c,
                delta=qty,
                cu=cu,
                stock_exists=existing is not None,
                afecta_costo=afecta_costo,
                es_movimiento_if=es_movimiento_if,
            )
            await _apply_delta(
                almacen_id,
                producto_id,
                qty,
                costo_promedio_objetivo=costo_obj,
            )

        for det in detalles:
            producto_id = det.get("producto_id")
            qty = _to_decimal(det.get("cantidad_base"), "0")
            cu = _to_decimal(det.get("costo_unitario"), "0")
            if not producto_id or qty == 0:
                continue

            if clase == "entrada":
                if not almacen_destino_id:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Movimiento de entrada requiere almacen_destino_id",
                    )
                await _apply_entrada_o_ajuste_positivo(
                    almacen_destino_id, producto_id, qty, cu
                )
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
                orig_row = await _fetch_stock(almacen_origen_id, producto_id)
                c_orig = (
                    _to_decimal(orig_row.get("costo_promedio"))
                    if orig_row
                    else Decimal("0")
                )
                await _apply_delta(almacen_origen_id, producto_id, -qty)
                dest_row = await _fetch_stock(almacen_destino_id, producto_id)
                q_dest = (
                    _to_decimal(dest_row.get("cantidad_actual"))
                    if dest_row
                    else Decimal("0")
                )
                c_dest = (
                    _to_decimal(dest_row.get("costo_promedio"))
                    if dest_row
                    else Decimal("0")
                )
                costo_dest = _resolve_costo_transferencia_destino(
                    q_dest=q_dest,
                    c_dest=c_dest,
                    delta=qty,
                    cu_eff=c_orig,
                    dest_exists=dest_row is not None,
                    afecta_costo=afecta_costo,
                )
                await _apply_delta(
                    almacen_destino_id,
                    producto_id,
                    qty,
                    costo_promedio_objetivo=costo_dest,
                )
            elif clase == "ajuste":
                target_almacen = almacen_destino_id or almacen_origen_id
                if not target_almacen:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Ajuste requiere almacen_origen_id o almacen_destino_id",
                    )
                if qty > 0:
                    await _apply_entrada_o_ajuste_positivo(
                        target_almacen, producto_id, qty, cu
                    )
                else:
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
        assert_movimiento_autorizable(mov)
        return mov
    if estado in ("procesado", "anulado", "estornado"):
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
    if estado == "estornado":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede anular un movimiento estornado",
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


async def estornar_movimiento_servicio(
    client_id: UUID,
    movimiento_id: UUID,
    motivo: Optional[str] = None,
    usuario_estorno_id: Optional[UUID] = None,
) -> dict:
    """
    Estorna un movimiento procesado mediante compensatorio en UoW atómica (P0–P5).

    Secuencia: lock original → gates → idempotencia → X-08 → INSERT compensatorio
    → procesar(uow) → UPDATE estornado. Un solo commit.
    """
    empresa_id = require_session_empresa_id()

    async with unit_of_work(client_id=client_id) as uow:
        # P0 — lock pesimista del original
        locked_rows = await uow.execute(
            SQL_LOCK_MOVIMIENTO_ORIGINAL,
            {
                "cliente_id": client_id,
                "empresa_id": empresa_id,
                "movimiento_id": movimiento_id,
            },
        )
        original = locked_rows[0] if locked_rows else None
        if not original:
            raise NotFoundError(detail="Movimiento no encontrado")

        estado = (original.get("estado") or "").strip().lower()
        if estado == "estornado":
            raise ConflictError(
                detail="El movimiento ya fue estornado o existe un compensatorio vinculado.",
                internal_code=MOVIMIENTO_YA_ESTORNADO_CODE,
            )
        if estado != "procesado":
            raise ConflictError(
                detail=f"Solo se puede estornar un movimiento en estado 'procesado'. "
                f"Estado actual: '{original.get('estado')}'.",
                internal_code=ESTORNO_NO_PROCESADO_CODE,
            )

        # P0b — gates MVP
        assert_estorno_mvp_allowed(original)

        tipo_movimiento_id = original.get("tipo_movimiento_id")
        if not tipo_movimiento_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Movimiento sin tipo_movimiento_id",
            )

        tm_rows = await uow.execute(
            select(InvTipoMovimientoTable).where(
                and_(
                    InvTipoMovimientoTable.c.cliente_id == client_id,
                    InvTipoMovimientoTable.c.empresa_id == empresa_id,
                    InvTipoMovimientoTable.c.tipo_movimiento_id == tipo_movimiento_id,
                )
            )
        )
        tipo_movimiento = tm_rows[0] if tm_rows else None
        if not tipo_movimiento:
            raise NotFoundError(detail="Tipo de movimiento no encontrado")

        detalles_rows = await uow.execute(
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
        if not detalles_rows:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se puede estornar un movimiento sin detalle",
            )

        # P1 — idempotencia compensatorio
        compensatorio_existente = await find_compensatorio_by_original(
            uow,
            client_id=client_id,
            empresa_id=empresa_id,
            original_movimiento_id=movimiento_id,
        )
        assert_compensatorio_no_existe(compensatorio_existente)

        # P0c — gate X-08 pre-PPM
        await assert_entrada_espejo_ppm_viable(
            client_id=client_id,
            empresa_id=empresa_id,
            tipo_movimiento=tipo_movimiento,
            movimiento=original,
            detalles=detalles_rows,
        )

        clase = (tipo_movimiento.get("clase_movimiento") or "").lower()
        now = datetime.utcnow()
        compensatorio_id = uuid.uuid4()
        detalles_espejo = build_compensatorio_detalles(detalles_rows, clase)
        if not detalles_espejo:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se puede estornar un movimiento sin líneas con cantidad",
            )

        usuario = usuario_estorno_id
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="usuario_estorno_id es requerido para estornar",
            )

        cabecera = build_compensatorio_cabecera_espejo(
            original=original,
            clase_movimiento=clase,
            motivo=motivo,
            usuario_estorno=usuario,
            compensatorio_movimiento_id=compensatorio_id,
            numero_movimiento=gen_numero_movimiento_estorno(),
            detalles_espejo=detalles_espejo,
            now=now,
        )

        # P2 — INSERT compensatorio
        cab_filtered = {k: v for k, v in cabecera.items() if k in _MOV_COLUMNS}
        await uow.execute(insert(InvMovimientoTable).values(**cab_filtered))

        # P3 — INSERT detalle espejo
        for det in detalles_espejo:
            det_values = {
                **det,
                "cliente_id": client_id,
                "empresa_id": empresa_id,
                "movimiento_id": compensatorio_id,
                "fecha_actualizacion": now,
            }
            det_filtered = {k: v for k, v in det_values.items() if k in _MOV_DET_COLUMNS}
            await uow.execute(insert(InvMovimientoDetalleTable).values(**det_filtered))

        # P4 — procesar compensatorio (único motor de mutación stock)
        await procesar_movimiento_servicio(
            client_id=client_id,
            movimiento_id=compensatorio_id,
            usuario_procesado_id=usuario_estorno_id,
            uow=uow,
        )

        # P5 — marcar original estornado (condicional rows_affected=1)
        p5_result = await uow.execute(
            update(InvMovimientoTable)
            .where(
                and_(
                    InvMovimientoTable.c.cliente_id == client_id,
                    InvMovimientoTable.c.empresa_id == empresa_id,
                    InvMovimientoTable.c.movimiento_id == movimiento_id,
                    InvMovimientoTable.c.estado == "procesado",
                )
            )
            .values(
                estado="estornado",
                motivo_anulacion=motivo,
                fecha_actualizacion=now,
            )
        )
        if not isinstance(p5_result, dict) or p5_result.get("rows_affected") != 1:
            raise ConflictError(
                detail="No se pudo marcar el movimiento como estornado: "
                "fue modificado concurrentemente.",
                internal_code=ESTORNO_UPDATE_RACE_CODE,
            )

        final_rows = await uow.execute(
            select(InvMovimientoTable).where(
                and_(
                    InvMovimientoTable.c.cliente_id == client_id,
                    InvMovimientoTable.c.empresa_id == empresa_id,
                    InvMovimientoTable.c.movimiento_id == movimiento_id,
                )
            )
        )
        return final_rows[0] if final_rows else original
