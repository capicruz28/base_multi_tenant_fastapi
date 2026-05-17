# app/modules/inv/application/services/inventario_fisico_service.py
"""
Servicio de Inventario Físico (INV). client_id siempre desde contexto, nunca desde body.
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy import select, insert, update, delete, and_

from app.core.exceptions import NotFoundError
from app.core.application.unit_of_work import unit_of_work
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.tables_erp import (
    InvInventarioFisicoTable,
    InvInventarioFisicoDetalleTable,
)
from app.infrastructure.database.queries.inv import (
    list_inventarios_fisicos,
    get_inventario_fisico_by_id,
    create_inventario_fisico,
    update_inventario_fisico,
    get_inventario_fisico_con_detalles,
)
from app.modules.inv.presentation.schemas import (
    InventarioFisicoCreate,
    InventarioFisicoUpdate,
    InventarioFisicoRead,
    InventarioFisicoDetalleRead,
    InventarioFisicoConDetalleCreate,
    InventarioFisicoConDetalleUpdate,
    InventarioFisicoConDetalleRead,
)

_INV_COLUMNS = {c.name for c in InvInventarioFisicoTable.c}
_INV_DET_COLUMNS = {c.name for c in InvInventarioFisicoDetalleTable.c}


def _row_to_read(row: dict) -> InventarioFisicoRead:
    return InventarioFisicoRead(**row)


async def list_inventarios_fisicos_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[InventarioFisicoRead]:
    rows = await list_inventarios_fisicos(
        client_id=client_id,
        empresa_id=empresa_id,
        almacen_id=almacen_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    return [_row_to_read(r) for r in rows]


async def get_inventario_fisico_servicio(
    client_id: UUID,
    inventario_fisico_id: UUID,
) -> InventarioFisicoRead:
    row = await get_inventario_fisico_by_id(client_id=client_id, inventario_fisico_id=inventario_fisico_id)
    if not row:
        raise NotFoundError(detail="Inventario físico no encontrado")
    return _row_to_read(row)


async def create_inventario_fisico_servicio(
    client_id: UUID,
    data: InventarioFisicoCreate,
) -> InventarioFisicoRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
    payload = data.model_dump()
    row = await create_inventario_fisico(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_inventario_fisico_servicio(
    client_id: UUID,
    inventario_fisico_id: UUID,
    data: InventarioFisicoUpdate,
) -> InventarioFisicoRead:
    row = await get_inventario_fisico_by_id(client_id=client_id, inventario_fisico_id=inventario_fisico_id)
    if not row:
        raise NotFoundError(detail="Inventario físico no encontrado")
    # Lifecycle: impedir edición cuando ya fue ajustado o anulado
    estado_actual = (row.get("estado") or "").lower()
    if estado_actual in ("ajustado", "anulado"):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede editar un inventario físico en estado '{row.get('estado')}'",
        )
    if data.empresa_id is not None:
        await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
    payload = data.model_dump(exclude_unset=True)
    updated = await update_inventario_fisico(client_id=client_id, inventario_fisico_id=inventario_fisico_id, data=payload)
    return _row_to_read(updated)


async def anular_inventario_fisico_servicio(
    *,
    client_id: UUID,
    inventario_fisico_id: UUID,
) -> InventarioFisicoRead:
    """
    Anula un inventario físico (cambia estado a 'anulado').
    Regla conservadora:
    - Si está 'ajustado' (ya generó ajuste), no se permite anular.
    """
    row = await get_inventario_fisico_by_id(client_id=client_id, inventario_fisico_id=inventario_fisico_id)
    if not row:
        raise NotFoundError(detail="Inventario físico no encontrado")
    estado = (row.get("estado") or "").lower()
    if estado == "anulado":
        return _row_to_read(row)
    if estado == "ajustado":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede anular un inventario físico ajustado",
        )
    updated = await update_inventario_fisico(
        client_id=client_id,
        inventario_fisico_id=inventario_fisico_id,
        data={"estado": "anulado"},
    )
    return _row_to_read(updated)


async def finalizar_inventario_fisico_servicio(
    *,
    client_id: UUID,
    inventario_fisico_id: UUID,
) -> InventarioFisicoRead:
    """
    Finaliza el conteo de un inventario físico (estado 'en_proceso' → 'finalizado').
    El inventario queda listo para ser aprobado y generar el ajuste de stock.
    """
    row = await get_inventario_fisico_by_id(
        client_id=client_id, inventario_fisico_id=inventario_fisico_id
    )
    if not row:
        raise NotFoundError(detail="Inventario físico no encontrado")
    estado = (row.get("estado") or "").lower()
    if estado == "finalizado":
        return _row_to_read(row)
    if estado in ("ajustado", "anulado"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede finalizar un inventario físico en estado '{row.get('estado')}'",
        )
    updated = await update_inventario_fisico(
        client_id=client_id,
        inventario_fisico_id=inventario_fisico_id,
        data={"estado": "finalizado", "fecha_finalizacion": datetime.utcnow()},
    )
    return _row_to_read(updated)


# ============================================================================
# FUNCIONES CABECERA + DETALLE EMBEBIDO
# ============================================================================

def _inv_det_row_to_read(row: dict) -> InventarioFisicoDetalleRead:
    return InventarioFisicoDetalleRead(**row)


async def get_inventario_fisico_con_detalles_servicio(
    client_id: UUID,
    inventario_fisico_id: UUID,
) -> InventarioFisicoConDetalleRead:
    """Retorna cabecera + detalles. Lanza NotFoundError si no existe."""
    combined = await get_inventario_fisico_con_detalles(
        client_id=client_id, inventario_fisico_id=inventario_fisico_id
    )
    if not combined:
        raise NotFoundError(detail="Inventario físico no encontrado")
    detalles = [_inv_det_row_to_read(d) for d in combined.pop("detalles", [])]
    return InventarioFisicoConDetalleRead(**combined, detalles=detalles)


async def _insert_inventario_fisico_detalles(
    uow,
    *,
    client_id: UUID,
    empresa_id: UUID,
    inventario_fisico_id: UUID,
    detalles: list,
    now: datetime,
) -> None:
    """Inserta líneas de inventario físico dentro de una transacción UoW activa."""
    for det in detalles:
        values = {
            "inventario_fisico_detalle_id": uuid4(),
            "cliente_id": client_id,
            "empresa_id": empresa_id,
            "inventario_fisico_id": inventario_fisico_id,
            "producto_id": det.producto_id,
            "cantidad_sistema": det.cantidad_sistema,
            "cantidad_contada": det.cantidad_contada,
            "lote": det.lote,
            "fecha_vencimiento": det.fecha_vencimiento,
            "ubicacion_almacen": det.ubicacion_almacen,
            "costo_unitario": det.costo_unitario,
            "estado_conteo": det.estado_conteo or "pendiente",
            "contador_usuario_id": det.contador_usuario_id,
            "contador_nombre": det.contador_nombre,
            "fecha_conteo": det.fecha_conteo,
            "observaciones": det.observaciones,
            "motivo_diferencia": det.motivo_diferencia,
        }
        filtered = {k: v for k, v in values.items() if k in _INV_DET_COLUMNS}
        await uow.execute(insert(InvInventarioFisicoDetalleTable).values(**filtered))


async def create_inventario_fisico_con_detalles_servicio(
    client_id: UUID,
    data: InventarioFisicoConDetalleCreate,
) -> InventarioFisicoConDetalleRead:
    """
    Crea un inventario físico con sus líneas de conteo en una sola transacción.
    Las líneas son opcionales al crear (se pueden añadir/reemplazar en PUT posterior).
    """
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)

    cab_payload = data.model_dump(exclude={"detalles"})
    empresa_id = data.empresa_id
    detalles_data = data.detalles

    now = datetime.utcnow()
    inventario_fisico_id = uuid4()

    cab_payload.update(
        inventario_fisico_id=inventario_fisico_id,
        cliente_id=client_id,
    )
    cab_filtered = {k: v for k, v in cab_payload.items() if k in _INV_COLUMNS}

    async with unit_of_work(client_id=client_id) as uow:
        await uow.execute(insert(InvInventarioFisicoTable).values(**cab_filtered))

        if detalles_data:
            await _insert_inventario_fisico_detalles(
                uow,
                client_id=client_id,
                empresa_id=empresa_id,
                inventario_fisico_id=inventario_fisico_id,
                detalles=detalles_data,
                now=now,
            )

        cab_rows = await uow.execute(
            select(InvInventarioFisicoTable).where(
                and_(
                    InvInventarioFisicoTable.c.cliente_id == client_id,
                    InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
        )
        det_rows = await uow.execute(
            select(InvInventarioFisicoDetalleTable)
            .where(
                and_(
                    InvInventarioFisicoDetalleTable.c.cliente_id == client_id,
                    InvInventarioFisicoDetalleTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
            .order_by(InvInventarioFisicoDetalleTable.c.producto_id)
        )

    cab = cab_rows[0] if cab_rows else {}
    return InventarioFisicoConDetalleRead(
        **cab,
        detalles=[_inv_det_row_to_read(d) for d in det_rows],
    )


async def update_inventario_fisico_con_detalles_servicio(
    client_id: UUID,
    inventario_fisico_id: UUID,
    data: InventarioFisicoConDetalleUpdate,
) -> InventarioFisicoConDetalleRead:
    """
    Actualiza cabecera (estados permitidos: todos excepto 'ajustado' y 'anulado') y,
    si se proporcionan 'detalles', reemplaza todas las líneas existentes (replace-all).
    """
    row = await get_inventario_fisico_by_id(
        client_id=client_id, inventario_fisico_id=inventario_fisico_id
    )
    if not row:
        raise NotFoundError(detail="Inventario físico no encontrado")
    estado_actual = (row.get("estado") or "").lower()
    if estado_actual in ("ajustado", "anulado"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede editar un inventario físico en estado '{row.get('estado')}'",
        )

    if data.empresa_id is not None:
        await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)

    cab_payload = data.model_dump(exclude_unset=True, exclude={"detalles"})
    now = datetime.utcnow()
    detalles_data = data.detalles  # None = sin cambio; list = reemplazar

    async with unit_of_work(client_id=client_id) as uow:
        if detalles_data is not None:
            # Delete-all + re-insert (replace-all pattern)
            await uow.execute(
                delete(InvInventarioFisicoDetalleTable).where(
                    and_(
                        InvInventarioFisicoDetalleTable.c.cliente_id == client_id,
                        InvInventarioFisicoDetalleTable.c.inventario_fisico_id == inventario_fisico_id,
                    )
                )
            )
            empresa_id = cab_payload.get("empresa_id") or row.get("empresa_id")
            if detalles_data:
                await _insert_inventario_fisico_detalles(
                    uow,
                    client_id=client_id,
                    empresa_id=empresa_id,
                    inventario_fisico_id=inventario_fisico_id,
                    detalles=detalles_data,
                    now=now,
                )

        if cab_payload:
            cab_payload["fecha_actualizacion"] = now
            filtered = {
                k: v for k, v in cab_payload.items()
                if k in _INV_COLUMNS and k not in ("inventario_fisico_id", "cliente_id")
            }
            if filtered:
                await uow.execute(
                    update(InvInventarioFisicoTable)
                    .where(
                        and_(
                            InvInventarioFisicoTable.c.cliente_id == client_id,
                            InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                        )
                    )
                    .values(**filtered)
                )

        cab_rows = await uow.execute(
            select(InvInventarioFisicoTable).where(
                and_(
                    InvInventarioFisicoTable.c.cliente_id == client_id,
                    InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
        )
        det_rows = await uow.execute(
            select(InvInventarioFisicoDetalleTable)
            .where(
                and_(
                    InvInventarioFisicoDetalleTable.c.cliente_id == client_id,
                    InvInventarioFisicoDetalleTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
            .order_by(InvInventarioFisicoDetalleTable.c.producto_id)
        )

    cab = cab_rows[0] if cab_rows else {}
    return InventarioFisicoConDetalleRead(
        **cab,
        detalles=[_inv_det_row_to_read(d) for d in det_rows],
    )
