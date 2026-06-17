# app/modules/inv/application/services/movimiento_service.py
"""
Servicio de Movimiento (INV). client_id siempre desde contexto, nunca desde body.
Aislamiento multi-empresa: empresa_id desde sesión JWT (company_scope).
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional, Any, Union
from uuid import UUID, uuid4
from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy import select, insert, update, delete, and_

from app.core.exceptions import NotFoundError
from app.core.application.unit_of_work import unit_of_work
from app.core.tenant.company_scope import (
    require_session_empresa_id,
    enforce_body_empresa_matches_session,
    ensure_empresa_in_tenant,
)
from app.shared.pagination import ErpPaginationParams, ErpSortParams, build_paginated_response
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.infrastructure.database.tables_erp import (
    InvMovimientoTable,
    InvMovimientoDetalleTable,
)
from app.infrastructure.database.queries.inv import (
    list_movimientos,
    count_movimientos,
    get_movimiento_by_id,
    create_movimiento,
    update_movimiento,
    get_movimiento_con_detalles,
    get_moneda_by_codigo,
    get_tipo_movimiento_by_id,
    get_almacen_by_id,
    get_producto_by_id,
    get_unidad_medida_by_id,
)
from app.modules.inv.application.services.inv_audit_context import apply_create_audit
from app.modules.inv.application.services.inv_workflow_enforcement import (
    reject_movimiento_workflow_in_update,
    sanitize_movimiento_create_payload,
)
from app.modules.inv.presentation.schemas import (
    MovimientoCreate,
    MovimientoUpdate,
    MovimientoRead,
    MovimientoDetalleRead,
    MovimientoConDetalleCreate,
    MovimientoConDetalleUpdate,
    MovimientoConDetalleRead,
)

_MOV_COLUMNS = {c.name for c in InvMovimientoTable.c}
_MOV_DET_COLUMNS = {c.name for c in InvMovimientoDetalleTable.c}


def _row_to_read(row: dict) -> MovimientoRead:
    return MovimientoRead(**row)


async def _resolve_moneda_id(
    *,
    client_id: UUID,
    moneda_id: Optional[UUID],
    moneda_codigo: Optional[str],
) -> UUID:
    if moneda_id:
        return moneda_id
    codigo = (moneda_codigo or "").strip().upper() or "PEN"
    row = await get_moneda_by_codigo(client_id=client_id, codigo=codigo, solo_activos=True)
    if not row:
        from app.core.exceptions import ValidationError

        raise ValidationError(detail=f"Moneda no encontrada o inactiva: {codigo}")
    return row["moneda_id"]


async def _validate_movimiento_cabecera_refs(
    client_id: UUID,
    empresa_id: UUID,
    *,
    tipo_movimiento_id: UUID,
    almacen_origen_id: Optional[UUID] = None,
    almacen_destino_id: Optional[UUID] = None,
) -> None:
    tm = await get_tipo_movimiento_by_id(
        client_id=client_id,
        tipo_movimiento_id=tipo_movimiento_id,
        empresa_id=empresa_id,
    )
    if not tm:
        raise NotFoundError(detail="Tipo de movimiento no encontrado")
    for alm_id, label in (
        (almacen_origen_id, "Almacén origen"),
        (almacen_destino_id, "Almacén destino"),
    ):
        if alm_id is not None:
            alm = await get_almacen_by_id(
                client_id=client_id,
                almacen_id=alm_id,
                empresa_id=empresa_id,
            )
            if not alm:
                raise NotFoundError(detail=f"{label} no encontrado")


async def _validate_optional_list_filtros(
    client_id: UUID,
    empresa_id: UUID,
    *,
    tipo_movimiento_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
) -> None:
    if tipo_movimiento_id is not None:
        tm = await get_tipo_movimiento_by_id(
            client_id=client_id,
            tipo_movimiento_id=tipo_movimiento_id,
            empresa_id=empresa_id,
        )
        if not tm:
            raise NotFoundError(detail="Tipo de movimiento no encontrado")
    if almacen_id is not None:
        alm = await get_almacen_by_id(
            client_id=client_id,
            almacen_id=almacen_id,
            empresa_id=empresa_id,
        )
        if not alm:
            raise NotFoundError(detail="Almacén no encontrado")


async def _validate_detalle_embebido_line(
    client_id: UUID,
    empresa_id: UUID,
    det: Any,
) -> None:
    prod = await get_producto_by_id(
        client_id=client_id,
        producto_id=det.producto_id,
        empresa_id=empresa_id,
    )
    if not prod:
        raise NotFoundError(detail="Producto no encontrado")
    um = await get_unidad_medida_by_id(
        client_id=client_id,
        unidad_medida_id=det.unidad_medida_id,
        empresa_id=empresa_id,
    )
    if not um:
        raise NotFoundError(detail="Unidad de medida no encontrada")


async def list_movimientos_servicio(
    client_id: UUID,
    tipo_movimiento_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    pagination: Optional[ErpPaginationParams] = None,
    sort: Optional[ErpSortParams] = None,
) -> Union[List[MovimientoRead], ErpPaginatedResponse[MovimientoRead]]:
    empresa_id = require_session_empresa_id()
    await _validate_optional_list_filtros(
        client_id,
        empresa_id,
        tipo_movimiento_id=tipo_movimiento_id,
        almacen_id=almacen_id,
    )
    sort_by = sort.sort_by if sort else None
    sort_dir = sort.sort_dir if sort and sort.is_active else None
    filtros = dict(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_movimiento_id=tipo_movimiento_id,
        almacen_id=almacen_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    list_filtros = {**filtros, "sort_by": sort_by, "sort_dir": sort_dir}
    if pagination is None or not pagination.is_paginated:
        rows = await list_movimientos(**list_filtros)
        return [_row_to_read(r) for r in rows]
    total = await count_movimientos(**filtros)
    rows = await list_movimientos(**list_filtros, pagination=pagination)
    items = [_row_to_read(r) for r in rows]
    return build_paginated_response(items, total, pagination)


async def get_movimiento_servicio(
    client_id: UUID,
    movimiento_id: UUID,
) -> MovimientoRead:
    empresa_id = require_session_empresa_id()
    row = await get_movimiento_by_id(
        client_id=client_id,
        movimiento_id=movimiento_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Movimiento no encontrado")
    return _row_to_read(row)


async def create_movimiento_servicio(
    client_id: UUID,
    data: MovimientoCreate,
    usuario_id: Optional[UUID] = None,
) -> MovimientoRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    await _validate_movimiento_cabecera_refs(
        client_id,
        empresa_id,
        tipo_movimiento_id=data.tipo_movimiento_id,
        almacen_origen_id=data.almacen_origen_id,
        almacen_destino_id=data.almacen_destino_id,
    )
    payload = sanitize_movimiento_create_payload(data.model_dump())
    payload["empresa_id"] = empresa_id
    payload["moneda_id"] = await _resolve_moneda_id(
        client_id=client_id,
        moneda_id=payload.get("moneda_id"),
        moneda_codigo=payload.get("moneda"),
    )
    payload = apply_create_audit(payload, usuario_id)
    row = await create_movimiento(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_movimiento_servicio(
    client_id: UUID,
    movimiento_id: UUID,
    data: MovimientoUpdate,
    usuario_id: Optional[UUID] = None,
) -> MovimientoRead:
    empresa_id = require_session_empresa_id()
    row = await get_movimiento_by_id(
        client_id=client_id,
        movimiento_id=movimiento_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Movimiento no encontrado")
    estado_actual = (row.get("estado") or "").lower()
    if estado_actual != "borrador":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede editar un movimiento que no esté en estado 'borrador'",
        )
    payload = data.model_dump(exclude_unset=True)
    reject_movimiento_workflow_in_update(payload)
    if payload.get("empresa_id") is not None:
        enforce_body_empresa_matches_session(payload["empresa_id"])
        payload["empresa_id"] = empresa_id
    tipo_id = payload.get("tipo_movimiento_id", row.get("tipo_movimiento_id"))
    if tipo_id:
        await _validate_movimiento_cabecera_refs(
            client_id,
            empresa_id,
            tipo_movimiento_id=tipo_id,
            almacen_origen_id=payload.get("almacen_origen_id", row.get("almacen_origen_id")),
            almacen_destino_id=payload.get("almacen_destino_id", row.get("almacen_destino_id")),
        )
    if "moneda_id" in payload or "moneda" in payload:
        payload["moneda_id"] = await _resolve_moneda_id(
            client_id=client_id,
            moneda_id=payload.get("moneda_id"),
            moneda_codigo=payload.get("moneda"),
        )
    updated = await update_movimiento(
        client_id=client_id,
        movimiento_id=movimiento_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)


def _det_row_to_read(row: dict) -> MovimientoDetalleRead:
    return MovimientoDetalleRead(**row)


async def get_movimiento_con_detalles_servicio(
    client_id: UUID,
    movimiento_id: UUID,
) -> MovimientoConDetalleRead:
    empresa_id = require_session_empresa_id()
    combined = await get_movimiento_con_detalles(
        client_id=client_id,
        movimiento_id=movimiento_id,
        empresa_id=empresa_id,
    )
    if not combined:
        raise NotFoundError(detail="Movimiento no encontrado")
    detalles = [_det_row_to_read(d) for d in combined.pop("detalles", [])]
    return MovimientoConDetalleRead(**combined, detalles=detalles)


async def _insert_movimiento_detalles(
    uow,
    *,
    client_id: UUID,
    empresa_id: UUID,
    movimiento_id: UUID,
    detalles: list,
    cabecera_moneda_id: UUID,
    now: datetime,
) -> None:
    for det in detalles:
        await _validate_detalle_embebido_line(client_id, empresa_id, det)
        det_moneda_id = det.moneda_id or cabecera_moneda_id
        values = {
            "movimiento_detalle_id": uuid4(),
            "cliente_id": client_id,
            "empresa_id": empresa_id,
            "movimiento_id": movimiento_id,
            "producto_id": det.producto_id,
            "cantidad": det.cantidad,
            "unidad_medida_id": det.unidad_medida_id,
            "cantidad_base": det.cantidad_base,
            "costo_unitario": det.costo_unitario
            if det.costo_unitario is not None
            else Decimal("0"),
            "moneda_id": det_moneda_id,
            "moneda": det.moneda or "PEN",
            "lote": det.lote,
            "fecha_vencimiento": det.fecha_vencimiento,
            "numero_serie": det.numero_serie,
            "ubicacion_almacen": det.ubicacion_almacen,
            "observaciones": det.observaciones,
            "fecha_actualizacion": now,
        }
        filtered = {k: v for k, v in values.items() if k in _MOV_DET_COLUMNS}
        await uow.execute(insert(InvMovimientoDetalleTable).values(**filtered))


async def create_movimiento_con_detalles_servicio(
    client_id: UUID,
    data: MovimientoConDetalleCreate,
    usuario_id: Optional[UUID] = None,
) -> MovimientoConDetalleRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    await _validate_movimiento_cabecera_refs(
        client_id,
        empresa_id,
        tipo_movimiento_id=data.tipo_movimiento_id,
        almacen_origen_id=data.almacen_origen_id,
        almacen_destino_id=data.almacen_destino_id,
    )

    cab_payload = sanitize_movimiento_create_payload(
        data.model_dump(exclude={"detalles"})
    )
    cab_payload["moneda_id"] = await _resolve_moneda_id(
        client_id=client_id,
        moneda_id=cab_payload.get("moneda_id"),
        moneda_codigo=cab_payload.get("moneda"),
    )
    cab_payload = apply_create_audit(cab_payload, usuario_id)
    cabecera_moneda_id = cab_payload["moneda_id"]
    detalles_data = data.detalles

    now = datetime.utcnow()
    movimiento_id = uuid4()

    cab_payload.update(
        movimiento_id=movimiento_id,
        cliente_id=client_id,
        empresa_id=empresa_id,
        total_items=len(detalles_data),
        total_cantidad=sum(d.cantidad_base for d in detalles_data),
        total_costo=sum(
            d.cantidad_base * (d.costo_unitario or Decimal("0"))
            for d in detalles_data
        ),
        fecha_actualizacion=now,
    )
    cab_filtered = {k: v for k, v in cab_payload.items() if k in _MOV_COLUMNS}

    async with unit_of_work(client_id=client_id) as uow:
        await uow.execute(insert(InvMovimientoTable).values(**cab_filtered))

        await _insert_movimiento_detalles(
            uow,
            client_id=client_id,
            empresa_id=empresa_id,
            movimiento_id=movimiento_id,
            detalles=detalles_data,
            cabecera_moneda_id=cabecera_moneda_id,
            now=now,
        )

        cab_rows = await uow.execute(
            select(InvMovimientoTable).where(
                and_(
                    InvMovimientoTable.c.cliente_id == client_id,
                    InvMovimientoTable.c.empresa_id == empresa_id,
                    InvMovimientoTable.c.movimiento_id == movimiento_id,
                )
            )
        )
        det_rows = await uow.execute(
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

    cab = cab_rows[0] if cab_rows else {}
    return MovimientoConDetalleRead(
        **cab,
        detalles=[_det_row_to_read(d) for d in det_rows],
    )


async def update_movimiento_con_detalles_servicio(
    client_id: UUID,
    movimiento_id: UUID,
    data: MovimientoConDetalleUpdate,
    usuario_id: Optional[UUID] = None,
) -> MovimientoConDetalleRead:
    empresa_id = require_session_empresa_id()
    row = await get_movimiento_by_id(
        client_id=client_id,
        movimiento_id=movimiento_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Movimiento no encontrado")
    estado_actual = (row.get("estado") or "").lower()
    if estado_actual != "borrador":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede editar un movimiento que no esté en estado 'borrador'",
        )

    cab_payload = data.model_dump(exclude_unset=True, exclude={"detalles"})
    reject_movimiento_workflow_in_update(cab_payload)
    if cab_payload.get("empresa_id") is not None:
        enforce_body_empresa_matches_session(cab_payload["empresa_id"])
    if "moneda_id" in cab_payload or "moneda" in cab_payload:
        cab_payload["moneda_id"] = await _resolve_moneda_id(
            client_id=client_id,
            moneda_id=cab_payload.get("moneda_id"),
            moneda_codigo=cab_payload.get("moneda"),
        )

    now = datetime.utcnow()
    detalles_data = data.detalles

    async with unit_of_work(client_id=client_id) as uow:
        if detalles_data is not None:
            await uow.execute(
                delete(InvMovimientoDetalleTable).where(
                    and_(
                        InvMovimientoDetalleTable.c.cliente_id == client_id,
                        InvMovimientoDetalleTable.c.empresa_id == empresa_id,
                        InvMovimientoDetalleTable.c.movimiento_id == movimiento_id,
                    )
                )
            )
            cabecera_moneda_id = cab_payload.get("moneda_id") or row.get("moneda_id")

            if detalles_data:
                await _insert_movimiento_detalles(
                    uow,
                    client_id=client_id,
                    empresa_id=empresa_id,
                    movimiento_id=movimiento_id,
                    detalles=detalles_data,
                    cabecera_moneda_id=cabecera_moneda_id,
                    now=now,
                )

            cab_payload.update(
                total_items=len(detalles_data),
                total_cantidad=sum(d.cantidad_base for d in detalles_data),
                total_costo=sum(
                    d.cantidad_base * (d.costo_unitario or Decimal("0"))
                    for d in detalles_data
                ),
            )

        if cab_payload:
            cab_payload["fecha_actualizacion"] = now
            if cab_payload.get("empresa_id") is not None:
                cab_payload["empresa_id"] = empresa_id
            tipo_id = cab_payload.get("tipo_movimiento_id", row.get("tipo_movimiento_id"))
            if tipo_id:
                await _validate_movimiento_cabecera_refs(
                    client_id,
                    empresa_id,
                    tipo_movimiento_id=tipo_id,
                    almacen_origen_id=cab_payload.get(
                        "almacen_origen_id", row.get("almacen_origen_id")
                    ),
                    almacen_destino_id=cab_payload.get(
                        "almacen_destino_id", row.get("almacen_destino_id")
                    ),
                )
            filtered = {
                k: v
                for k, v in cab_payload.items()
                if k in _MOV_COLUMNS and k not in ("movimiento_id", "cliente_id")
            }
            if filtered:
                await uow.execute(
                    update(InvMovimientoTable)
                    .where(
                        and_(
                            InvMovimientoTable.c.cliente_id == client_id,
                            InvMovimientoTable.c.empresa_id == empresa_id,
                            InvMovimientoTable.c.movimiento_id == movimiento_id,
                        )
                    )
                    .values(**filtered)
                )

        cab_rows = await uow.execute(
            select(InvMovimientoTable).where(
                and_(
                    InvMovimientoTable.c.cliente_id == client_id,
                    InvMovimientoTable.c.empresa_id == empresa_id,
                    InvMovimientoTable.c.movimiento_id == movimiento_id,
                )
            )
        )
        det_rows = await uow.execute(
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

    cab = cab_rows[0] if cab_rows else {}
    return MovimientoConDetalleRead(
        **cab,
        detalles=[_det_row_to_read(d) for d in det_rows],
    )
