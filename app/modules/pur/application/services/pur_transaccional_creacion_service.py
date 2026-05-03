# app/modules/pur/application/services/pur_transaccional_creacion_service.py
"""
Creación cabecera + detalle PUR en una sola transacción atómica.

Objetivo: evitar inconsistencias (cabeceras sin detalle o detalle incompleto)
sin romper los endpoints legacy existentes.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import insert
from sqlalchemy.sql.schema import Table

from app.core.application.unit_of_work import UnitOfWork
from app.core.exceptions import NotFoundError
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.tables_erp.tables_pur import (
    PurCotizacionDetalleTable,
    PurCotizacionTable,
    PurOrdenCompraDetalleTable,
    PurOrdenCompraTable,
    PurRecepcionDetalleTable,
    PurRecepcionTable,
    PurSolicitudCompraDetalleTable,
    PurSolicitudCompraTable,
)
from app.infrastructure.database.queries.inv import (
    get_almacen_by_id,
    get_producto_by_id,
    get_unidad_medida_by_id,
)
from app.infrastructure.database.queries.pur import (
    get_cotizacion_by_id,
    get_orden_compra_by_id,
    get_orden_compra_detalle_by_id,
    get_proveedor_by_id,
    get_recepcion_by_id,
    get_solicitud_by_id,
)
from app.modules.pur.presentation.schemas import (
    CotizacionDetalleItemTransaccionalCreate,
    CotizacionRead,
    CotizacionTransaccionalCreate,
    OrdenCompraDetalleItemTransaccionalCreate,
    OrdenCompraRead,
    OrdenCompraTransaccionalCreate,
    RecepcionDetalleItemTransaccionalCreate,
    RecepcionRead,
    RecepcionTransaccionalCreate,
    SolicitudCompraDetalleItemTransaccionalCreate,
    SolicitudCompraRead,
    SolicitudCompraTransaccionalCreate,
)


def _table_columns(table: Table) -> Set[str]:
    return {c.name for c in table.c}


def _filter_payload(payload: Dict[str, Any], table: Table) -> Dict[str, Any]:
    cols = _table_columns(table)
    return {k: v for k, v in payload.items() if k in cols}


def _validate_estado(value: Optional[str], allowed: Sequence[str], field_name: str) -> Optional[str]:
    if value is None:
        return None
    normalized = (value or "").strip().lower()
    allowed_norm = {a.lower() for a in allowed}
    if normalized not in allowed_norm:
        raise HTTPException(
            status_code=422,
            detail=f"Estado inválido para {field_name}. Se permite: {sorted(allowed)}",
        )
    return normalized


async def _require_row(row: Optional[Dict[str, Any]], not_found_detail: str) -> Dict[str, Any]:
    if not row:
        raise NotFoundError(detail=not_found_detail)
    return row


def _to_decimal(value: Any, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


async def _validate_producto_y_um(
    client_id: UUID,
    empresa_id: UUID,
    items: Iterable[Dict[str, Any]],
) -> None:
    # Valida producto_id y unidad_medida_id vs empresa_id.
    # Nota: esto evita que se inserte detalle cruzando empresas dentro del mismo tenant.
    for item in items:
        producto_id = item.get("producto_id")
        unidad_medida_id = item.get("unidad_medida_id")

        if not producto_id:
            raise HTTPException(status_code=422, detail="Detalle incompleto: falta producto_id")
        if not unidad_medida_id:
            raise HTTPException(status_code=422, detail="Detalle incompleto: falta unidad_medida_id")

        prod = await get_producto_by_id(client_id=client_id, producto_id=producto_id)
        prod = await _require_row(prod, "Producto no encontrado")
        if prod.get("empresa_id") != empresa_id:
            raise HTTPException(
                status_code=422,
                detail="Producto no pertenece a empresa_id de la cabecera",
            )

        um = await get_unidad_medida_by_id(client_id=client_id, unidad_medida_id=unidad_medida_id)
        um = await _require_row(um, "Unidad de medida no encontrada")
        if um.get("empresa_id") != empresa_id:
            raise HTTPException(
                status_code=422,
                detail="Unidad de medida no pertenece a empresa_id de la cabecera",
            )


async def _validate_proveedor(
    client_id: UUID,
    empresa_id: UUID,
    proveedor_id: UUID,
) -> Dict[str, Any]:
    prov = await get_proveedor_by_id(client_id=client_id, proveedor_id=proveedor_id)
    prov = await _require_row(prov, "Proveedor no encontrado")
    if prov.get("empresa_id") != empresa_id:
        raise HTTPException(status_code=422, detail="Proveedor no pertenece a empresa_id de la cabecera")
    return prov


async def _validate_almacen(
    client_id: UUID,
    empresa_id: UUID,
    almacen_id: UUID,
) -> Dict[str, Any]:
    alm = await get_almacen_by_id(client_id=client_id, almacen_id=almacen_id)
    alm = await _require_row(alm, "Almacén no encontrado")
    if alm.get("empresa_id") != empresa_id:
        raise HTTPException(status_code=422, detail="Almacén no pertenece a empresa_id de la cabecera")
    return alm


async def _create_header_with_details(
    *,
    client_id: UUID,
    empresa_id: UUID,
    uow: UnitOfWork,
    header_table: Table,
    detail_table: Table,
    header_pk_field: str,
    detail_pk_field: str,
    detail_parent_field: str,
    header_payload: Dict[str, Any],
    detail_items_payload: Sequence[Dict[str, Any]],
) -> UUID:
    if not detail_items_payload:
        raise HTTPException(status_code=422, detail="No se puede crear una cabecera sin detalle")

    header_id = uuid4()

    # Insert cabecera
    cab_payload = dict(header_payload)
    cab_payload[header_pk_field] = header_id
    cab_payload["cliente_id"] = client_id
    cab_payload["empresa_id"] = empresa_id
    cab_payload = _filter_payload(cab_payload, header_table)

    await uow.execute(insert(header_table).values(**cab_payload))

    # Insert detalle
    for item_payload in detail_items_payload:
        det_payload = dict(item_payload)
        det_payload[detail_pk_field] = uuid4()
        det_payload["cliente_id"] = client_id
        det_payload["empresa_id"] = empresa_id
        det_payload[detail_parent_field] = header_id
        det_payload = _filter_payload(det_payload, detail_table)
        await uow.execute(insert(detail_table).values(**det_payload))

    return header_id


# ============================================================================
# SOLICITUD COMPRA (cabecera + detalle)
# ============================================================================


async def create_solicitud_transaccional_servicio(
    client_id: UUID,
    data: SolicitudCompraTransaccionalCreate,
) -> SolicitudCompraRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.cabecera.empresa_id)

    header = data.cabecera
    empresa_id = header.empresa_id

    allowed_estado = ["borrador", "pendiente_aprobacion", "aprobada", "rechazada", "procesada", "anulada"]
    estado_norm = _validate_estado(header.estado, allowed_estado, field_name="Solicitud.estado")
    # En caso de envío con case distinto, almacenamos normalizado.
    header_payload = header.model_dump(exclude_none=True)
    header_payload["estado"] = estado_norm or header_payload.get("estado")

    # Integridad cabecera-detalle
    detalle_items = data.detalle
    if not detalle_items:
        raise HTTPException(status_code=422, detail="No se puede crear una solicitud sin detalle")

    # Validaciones de detalle contra BD (producto + unidad pertenecen a empresa)
    await _validate_producto_y_um(
        client_id=client_id,
        empresa_id=empresa_id,
        items=[d.model_dump(exclude_none=True) for d in detalle_items],
    )

    # Protecciones extra: recalcular total_items si viene en 0/None
    header_payload["total_items"] = len(detalle_items)
    if header_payload.get("total_estimado") in (None, 0):
        total_estimado = Decimal("0")
        for d in detalle_items:
            precio_ref = d.precio_referencial or Decimal("0")
            total_estimado += _to_decimal(d.cantidad_solicitada) * _to_decimal(precio_ref)
        header_payload["total_estimado"] = total_estimado

    # Insert atómico
    async with UnitOfWork(client_id=client_id) as uow:
        solicitud_id = await _create_header_with_details(
            client_id=client_id,
            empresa_id=empresa_id,
            uow=uow,
            header_table=PurSolicitudCompraTable,
            detail_table=PurSolicitudCompraDetalleTable,
            header_pk_field="solicitud_id",
            detail_pk_field="solicitud_detalle_id",
            detail_parent_field="solicitud_id",
            header_payload=_filter_payload(header_payload, PurSolicitudCompraTable),
            detail_items_payload=[
                d.model_dump(exclude_none=True) for d in detalle_items
            ],
        )

    row = await get_solicitud_by_id(client_id=client_id, solicitud_id=solicitud_id)
    if not row:
        raise HTTPException(status_code=500, detail="No se pudo recuperar la solicitud creada")
    return SolicitudCompraRead(**row)


# ============================================================================
# COTIZACION (cabecera + detalle)
# ============================================================================


async def create_cotizacion_transaccional_servicio(
    client_id: UUID,
    data: CotizacionTransaccionalCreate,
) -> CotizacionRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.cabecera.empresa_id)

    header = data.cabecera
    empresa_id = header.empresa_id

    allowed_estado = ["pendiente", "recibida", "evaluada", "aceptada", "rechazada", "vencida"]
    estado_norm = _validate_estado(header.estado, allowed_estado, field_name="Cotizacion.estado")
    header_payload = header.model_dump(exclude_none=True)
    header_payload["estado"] = estado_norm or header_payload.get("estado")

    detalle_items = data.detalle
    if not detalle_items:
        raise HTTPException(status_code=422, detail="No se puede crear una cotización sin detalle")

    await _validate_proveedor(client_id=client_id, empresa_id=empresa_id, proveedor_id=header.proveedor_id)

    await _validate_producto_y_um(
        client_id=client_id,
        empresa_id=empresa_id,
        items=[d.model_dump(exclude_none=True) for d in detalle_items],
    )

    async with UnitOfWork(client_id=client_id) as uow:
        cotizacion_id = await _create_header_with_details(
            client_id=client_id,
            empresa_id=empresa_id,
            uow=uow,
            header_table=PurCotizacionTable,
            detail_table=PurCotizacionDetalleTable,
            header_pk_field="cotizacion_id",
            detail_pk_field="cotizacion_detalle_id",
            detail_parent_field="cotizacion_id",
            header_payload=_filter_payload(header_payload, PurCotizacionTable),
            detail_items_payload=[
                d.model_dump(exclude_none=True) for d in detalle_items
            ],
        )

    row = await get_cotizacion_by_id(client_id=client_id, cotizacion_id=cotizacion_id)
    if not row:
        raise HTTPException(status_code=500, detail="No se pudo recuperar la cotización creada")
    return CotizacionRead(**row)


# ============================================================================
# ORDEN DE COMPRA (cabecera + detalle)
# ============================================================================


async def create_orden_compra_transaccional_servicio(
    client_id: UUID,
    data: OrdenCompraTransaccionalCreate,
) -> OrdenCompraRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.cabecera.empresa_id)

    header = data.cabecera
    empresa_id = header.empresa_id

    # La OC se debe crear en borrador para que el flujo legacy de aprobación funcione.
    allowed_estado = ["borrador", "emitida", "aprobada", "parcial", "completa", "anulada"]
    estado_norm = _validate_estado(header.estado, allowed_estado, field_name="OrdenCompra.estado")
    if (estado_norm or "").lower() != "borrador":
        raise HTTPException(status_code=422, detail="La OC transaccional solo permite estado 'borrador'")

    header_payload = header.model_dump(exclude_none=True)
    header_payload["estado"] = estado_norm or header_payload.get("estado")

    detalle_items = data.detalle
    if not detalle_items:
        raise HTTPException(status_code=422, detail="No se puede crear una OC sin detalle")

    await _validate_proveedor(client_id=client_id, empresa_id=empresa_id, proveedor_id=header.proveedor_id)
    if header.almacen_destino_id:
        await _validate_almacen(client_id=client_id, empresa_id=empresa_id, almacen_id=header.almacen_destino_id)

    # Validar producto + unidad por línea.
    await _validate_producto_y_um(
        client_id=client_id,
        empresa_id=empresa_id,
        items=[d.model_dump(exclude_none=True) for d in detalle_items],
    )

    # Insert atómico
    header_payload["total_items"] = len(detalle_items)
    async with UnitOfWork(client_id=client_id) as uow:
        oc_id = await _create_header_with_details(
            client_id=client_id,
            empresa_id=empresa_id,
            uow=uow,
            header_table=PurOrdenCompraTable,
            detail_table=PurOrdenCompraDetalleTable,
            header_pk_field="orden_compra_id",
            detail_pk_field="orden_compra_detalle_id",
            detail_parent_field="orden_compra_id",
            header_payload=_filter_payload(header_payload, PurOrdenCompraTable),
            detail_items_payload=[
                d.model_dump(exclude_none=True) for d in detalle_items
            ],
        )

    row = await get_orden_compra_by_id(client_id=client_id, orden_compra_id=oc_id)
    if not row:
        raise HTTPException(status_code=500, detail="No se pudo recuperar la orden de compra creada")
    return OrdenCompraRead(**row)


# ============================================================================
# RECEPCION (cabecera + detalle)
# ============================================================================


async def create_recepcion_transaccional_servicio(
    client_id: UUID,
    data: RecepcionTransaccionalCreate,
) -> RecepcionRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.cabecera.empresa_id)

    header = data.cabecera
    empresa_id = header.empresa_id

    # La recepción debe nacer en borrador para que el endpoint /procesar genere movimiento INV.
    allowed_estado = ["borrador", "procesada", "inspeccion", "aprobada", "anulada"]
    estado_norm = _validate_estado(header.estado, allowed_estado, field_name="Recepcion.estado")
    if (estado_norm or "").lower() != "borrador":
        raise HTTPException(status_code=422, detail="La recepción transaccional solo permite estado 'borrador'")

    header_payload = header.model_dump(exclude_none=True)
    header_payload["estado"] = estado_norm or header_payload.get("estado")

    detalle_items = data.detalle
    if not detalle_items:
        raise HTTPException(status_code=422, detail="No se puede crear una recepción sin detalle")

    # Validar cabeceras referenciadas (OC, proveedor, almacén).
    oc = await get_orden_compra_by_id(client_id=client_id, orden_compra_id=header.orden_compra_id)
    oc = await _require_row(oc, "OC no encontrada")
    if oc.get("empresa_id") != empresa_id:
        raise HTTPException(status_code=422, detail="OC no pertenece a empresa_id de la cabecera")

    await _validate_proveedor(client_id=client_id, empresa_id=empresa_id, proveedor_id=header.proveedor_id)

    await _validate_almacen(client_id=client_id, empresa_id=empresa_id, almacen_id=header.almacen_id)

    # Validar producto/unidad de medida de cada línea contra empresa_id.
    await _validate_producto_y_um(
        client_id=client_id,
        empresa_id=empresa_id,
        items=[d.model_dump(exclude_none=True) for d in detalle_items],
    )

    # Validar y asegurar integridad por cada línea contra la OC detalle.
    detalle_payloads: List[Dict[str, Any]] = []
    acumulado_rec: Dict[UUID, Decimal] = {}
    for item in detalle_items:
        item_payload = item.model_dump(exclude_none=True)
        ocdet_id = item_payload.get("orden_compra_detalle_id")
        if not ocdet_id:
            raise HTTPException(status_code=422, detail="Detalle incompleto: falta orden_compra_detalle_id")

        ocdet = await get_orden_compra_detalle_by_id(client_id=client_id, orden_compra_detalle_id=ocdet_id)
        ocdet = await _require_row(ocdet, "Detalle OC no encontrado")

        if ocdet.get("empresa_id") != empresa_id:
            raise HTTPException(status_code=422, detail="Detalle OC no pertenece a la empresa")
        if ocdet.get("orden_compra_id") != header.orden_compra_id:
            raise HTTPException(status_code=422, detail="Detalle OC no pertenece a la OC indicada")

        if item_payload.get("producto_id") != ocdet.get("producto_id"):
            raise HTTPException(status_code=422, detail="producto_id no coincide con el detalle de OC")
        if item_payload.get("unidad_medida_id") != ocdet.get("unidad_medida_id"):
            raise HTTPException(status_code=422, detail="unidad_medida_id no coincide con el detalle de OC")

        # cantidad_ordenada debe ser consistente con OC.
        if _to_decimal(item_payload.get("cantidad_ordenada")) != _to_decimal(ocdet.get("cantidad_ordenada")):
            raise HTTPException(status_code=422, detail="cantidad_ordenada no coincide con la OC")

        # Validar no exceder la cantidad de OC (considerando recepciones previas).
        prev_rec = _to_decimal(ocdet.get("cantidad_recepcionada"))
        nuevo_rec = _to_decimal(item_payload.get("cantidad_recepcionada"))
        ya_incluido = acumulado_rec.get(ocdet_id, Decimal("0"))
        new_rec_total = prev_rec + ya_incluido + nuevo_rec
        if new_rec_total > _to_decimal(ocdet.get("cantidad_ordenada")):
            raise HTTPException(
                status_code=422,
                detail="cantidad_recepcionada excede la cantidad ordenada de la OC",
            )

        acumulado_rec[ocdet_id] = ya_incluido + nuevo_rec
        detalle_payloads.append(item_payload)

    # Recalcular totales de cabecera si vienen en 0/None.
    header_payload["total_items"] = len(detalle_payloads)
    if header_payload.get("total_cantidad") in (None, 0):
        total_cantidad = sum(_to_decimal(d.get("cantidad_recepcionada")) for d in detalle_payloads)
        header_payload["total_cantidad"] = total_cantidad

    async with UnitOfWork(client_id=client_id) as uow:
        recepcion_id = await _create_header_with_details(
            client_id=client_id,
            empresa_id=empresa_id,
            uow=uow,
            header_table=PurRecepcionTable,
            detail_table=PurRecepcionDetalleTable,
            header_pk_field="recepcion_id",
            detail_pk_field="recepcion_detalle_id",
            detail_parent_field="recepcion_id",
            header_payload=_filter_payload(header_payload, PurRecepcionTable),
            detail_items_payload=detalle_payloads,
        )

    row = await get_recepcion_by_id(client_id=client_id, recepcion_id=recepcion_id)
    if not row:
        raise HTTPException(status_code=500, detail="No se pudo recuperar la recepción creada")
    return RecepcionRead(**row)

