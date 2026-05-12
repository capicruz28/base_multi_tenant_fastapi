# app/modules/pur/application/services/recepcion_service.py
"""
Servicio de Recepción (PUR). client_id siempre desde contexto, nunca desde body.
Integración con INV: al procesar se genera movimiento de entrada y se actualiza OC.
"""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime

from fastapi import HTTPException, status

from app.core.exceptions import NotFoundError
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.pur import (
    list_recepciones,
    get_recepcion_by_id,
    create_recepcion,
    update_recepcion,
    list_recepciones_detalle,
    get_orden_compra_detalle_by_id,
    update_orden_compra_detalle,
    get_orden_compra_by_id,
    update_orden_compra,
    list_ordenes_compra_detalle,
)
from app.infrastructure.database.queries.inv import (
    list_tipos_movimiento,
    create_movimiento,
    create_movimiento_detalle,
)
from app.modules.inv.application.services.movimiento_proceso_service import (
    procesar_movimiento_servicio,
)
from app.modules.pur.presentation.schemas import (
    RecepcionCreate,
    RecepcionUpdate,
    RecepcionRead,
)


def _to_decimal(value, default="0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _estado_recepcion_norm(estado: Optional[str]) -> str:
    return (estado or "").strip().lower()


def _row_to_read(row: dict) -> RecepcionRead:
    return RecepcionRead(**row)


async def list_recepciones_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    orden_compra_id: Optional[UUID] = None,
    proveedor_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    sort_by: Optional[str] = None,
    order: Optional[str] = None,
) -> List[RecepcionRead]:
    skip = (page - 1) * page_size if page is not None and page_size is not None else None
    limit = page_size if page_size is not None else None
    rows = await list_recepciones(
        client_id=client_id,
        empresa_id=empresa_id,
        orden_compra_id=orden_compra_id,
        proveedor_id=proveedor_id,
        almacen_id=almacen_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order,
    )
    return [_row_to_read(r) for r in rows]


async def get_recepcion_servicio(
    client_id: UUID,
    recepcion_id: UUID,
) -> RecepcionRead:
    row = await get_recepcion_by_id(client_id=client_id, recepcion_id=recepcion_id)
    if not row:
        raise NotFoundError(detail="Recepción no encontrada")
    return _row_to_read(row)


async def create_recepcion_servicio(
    client_id: UUID,
    data: RecepcionCreate,
) -> RecepcionRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
    payload = data.model_dump()
    row = await create_recepcion(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_recepcion_servicio(
    client_id: UUID,
    recepcion_id: UUID,
    data: RecepcionUpdate,
) -> RecepcionRead:
    row = await get_recepcion_by_id(client_id=client_id, recepcion_id=recepcion_id)
    if not row:
        raise NotFoundError(detail="Recepción no encontrada")
    payload = data.model_dump(exclude_unset=True)
    if payload and _estado_recepcion_norm(row.get("estado")) != "borrador":
        raise ValueError("Solo se puede editar la recepción en estado borrador")
    updated = await update_recepcion(client_id=client_id, recepcion_id=recepcion_id, data=payload)
    return _row_to_read(updated)


async def procesar_recepcion_servicio(
    client_id: UUID,
    recepcion_id: UUID,
    usuario_procesado_id: UUID,
) -> RecepcionRead:
    row = await get_recepcion_by_id(client_id=client_id, recepcion_id=recepcion_id)
    if not row:
        raise NotFoundError(detail="Recepción no encontrada")
    st = _estado_recepcion_norm(row.get("estado"))
    if st == "procesada":
        return _row_to_read(row)
    if st != "borrador":
        raise ValueError("Solo se puede procesar una recepción en estado borrador")

    detalle = await list_recepciones_detalle(
        client_id=client_id, recepcion_id=recepcion_id
    )
    if not detalle:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se puede procesar una recepción sin detalle",
        )

    empresa_id = row["empresa_id"]
    almacen_id = row.get("almacen_id")
    if not almacen_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Recepción sin almacén de destino",
        )

    tipos = await list_tipos_movimiento(
        client_id=client_id, empresa_id=empresa_id, solo_activos=True
    )
    tipo_entrada = next(
        (t for t in tipos if (t.get("clase_movimiento") or "").lower() == "entrada"),
        None,
    )
    if not tipo_entrada:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No existe tipo de movimiento 'entrada' configurado para la empresa",
        )
    tipo_movimiento_id = tipo_entrada["tipo_movimiento_id"]

    numero_recepcion = (row.get("numero_recepcion") or "REC").replace(" ", "-")
    numero_movimiento = f"PUR-{numero_recepcion}"

    fecha_contable = datetime.utcnow().date()
    total_cantidad = sum(_to_decimal(d.get("cantidad_recepcionada")) for d in detalle)
    total_items = len(detalle)

    mov_data = {
        "empresa_id": empresa_id,
        "numero_movimiento": numero_movimiento[:20],
        "tipo_movimiento_id": tipo_movimiento_id,
        "fecha_movimiento": datetime.utcnow(),
        "fecha_contable": fecha_contable,
        "almacen_origen_id": None,
        "almacen_destino_id": almacen_id,
        "modulo_origen": "PUR",
        "documento_referencia_tipo": "RECEPCION",
        "documento_referencia_id": recepcion_id,
        "documento_referencia_numero": str(numero_recepcion)[:30],
        "tercero_tipo": "PROVEEDOR",
        "tercero_id": row.get("proveedor_id"),
        "tercero_nombre": (row.get("recepcionado_por_nombre") or "")[:200],
        "total_items": total_items,
        "total_cantidad": total_cantidad,
        "total_costo": Decimal("0"),
        "moneda": "PEN",
        "estado": "borrador",
        "usuario_creacion_id": usuario_procesado_id,
    }
    mov = await create_movimiento(client_id=client_id, data=mov_data)
    movimiento_id = mov["movimiento_id"]

    for d in detalle:
        cantidad_rec = _to_decimal(d.get("cantidad_recepcionada"))
        if cantidad_rec <= 0:
            continue
        await create_movimiento_detalle(
            client_id=client_id,
            data={
                "empresa_id": empresa_id,
                "movimiento_id": movimiento_id,
                "producto_id": d["producto_id"],
                "cantidad": cantidad_rec,
                "unidad_medida_id": d["unidad_medida_id"],
                "cantidad_base": cantidad_rec,
                "costo_unitario": _to_decimal(d.get("precio_unitario")),
                "moneda": "PEN",
                "lote": d.get("lote"),
                "fecha_vencimiento": d.get("fecha_vencimiento"),
                "ubicacion_almacen": d.get("ubicacion_almacen"),
                "observaciones": d.get("observaciones"),
            },
        )

    await procesar_movimiento_servicio(
        client_id=client_id,
        movimiento_id=movimiento_id,
        usuario_procesado_id=usuario_procesado_id,
    )

    payload_recep = {
        "estado": "procesada",
        "fecha_procesado": datetime.utcnow(),
        "usuario_procesado_id": usuario_procesado_id,
        "movimiento_inventario_id": movimiento_id,
    }
    updated = await update_recepcion(
        client_id=client_id, recepcion_id=recepcion_id, data=payload_recep
    )

    orden_compra_id = row.get("orden_compra_id")
    oc_row = None
    if orden_compra_id:
        oc_row = await get_orden_compra_by_id(client_id=client_id, orden_compra_id=orden_compra_id)
        for d in detalle:
            ocdet_id = d.get("orden_compra_detalle_id")
            if not ocdet_id:
                continue
            ocdet = await get_orden_compra_detalle_by_id(
                client_id=client_id, orden_compra_detalle_id=ocdet_id
            )
            if not ocdet:
                continue
            actual = _to_decimal(ocdet.get("cantidad_recepcionada"))
            nueva = actual + _to_decimal(d.get("cantidad_recepcionada"))
            await update_orden_compra_detalle(
                client_id=client_id,
                orden_compra_detalle_id=ocdet_id,
                data={"cantidad_recepcionada": nueva},
            )

        lineas_oc = await list_ordenes_compra_detalle(
            client_id=client_id, orden_compra_id=orden_compra_id
        )
        total_ordenado = sum(_to_decimal(l.get("cantidad_ordenada")) for l in lineas_oc)
        total_recibido = sum(_to_decimal(l.get("cantidad_recepcionada")) for l in lineas_oc)
        items_recepcionados = sum(
            1 for l in lineas_oc if _to_decimal(l.get("cantidad_recepcionada")) > 0
        )
        porcentaje = (
            (total_recibido / total_ordenado * 100) if total_ordenado > 0 else Decimal("0")
        )
        payload_oc = {
            "items_recepcionados": items_recepcionados,
            "porcentaje_recepcion": round(porcentaje, 2),
        }
        if oc_row and (oc_row.get("estado") or "").lower() != "anulada":
            payload_oc["estado"] = "completa" if porcentaje >= 100 else "parcial"
        await update_orden_compra(
            client_id=client_id,
            orden_compra_id=orden_compra_id,
            data=payload_oc,
        )

    return _row_to_read(updated)


async def anular_recepcion_servicio(
    client_id: UUID,
    recepcion_id: UUID,
) -> RecepcionRead:
    row = await get_recepcion_by_id(client_id=client_id, recepcion_id=recepcion_id)
    if not row:
        raise NotFoundError(detail="Recepción no encontrada")
    st = _estado_recepcion_norm(row.get("estado"))
    if st in ("procesada", "anulada"):
        raise ValueError("No se puede anular la recepción en su estado actual")
    updated = await update_recepcion(
        client_id=client_id,
        recepcion_id=recepcion_id,
        data={"estado": "anulada"},
    )
    return _row_to_read(updated)


async def aprobar_recepcion_servicio(
    client_id: UUID,
    recepcion_id: UUID,
) -> RecepcionRead:
    row = await get_recepcion_by_id(client_id=client_id, recepcion_id=recepcion_id)
    if not row:
        raise NotFoundError(detail="Recepción no encontrada")
    if _estado_recepcion_norm(row.get("estado")) != "inspeccion":
        raise ValueError("Solo se puede aprobar una recepción en estado inspección")
    updated = await update_recepcion(
        client_id=client_id,
        recepcion_id=recepcion_id,
        data={"estado": "aprobada"},
    )
    return _row_to_read(updated)
