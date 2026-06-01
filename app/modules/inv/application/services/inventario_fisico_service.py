# app/modules/inv/application/services/inventario_fisico_service.py
"""
Servicio de Inventario Físico (INV). client_id siempre desde contexto, nunca desde body.
Aislamiento multi-empresa: empresa_id desde sesión JWT (company_scope).
"""
from __future__ import annotations

from typing import List, Optional
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
    get_almacen_by_id,
    get_producto_by_id,
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


def _inv_det_row_to_read(row: dict) -> InventarioFisicoDetalleRead:
    return InventarioFisicoDetalleRead(**row)


async def _validate_optional_list_filtros(
    client_id: UUID,
    empresa_id: UUID,
    *,
    almacen_id: Optional[UUID] = None,
) -> None:
    if almacen_id is not None:
        alm = await get_almacen_by_id(
            client_id=client_id,
            almacen_id=almacen_id,
            empresa_id=empresa_id,
        )
        if not alm:
            raise NotFoundError(detail="Almacén no encontrado")


async def _validate_cabecera_refs(
    client_id: UUID,
    empresa_id: UUID,
    *,
    almacen_id: UUID,
) -> None:
    alm = await get_almacen_by_id(
        client_id=client_id,
        almacen_id=almacen_id,
        empresa_id=empresa_id,
    )
    if not alm:
        raise NotFoundError(detail="Almacén no encontrado")


async def _validate_detalle_productos(
    client_id: UUID,
    empresa_id: UUID,
    detalles: list,
) -> None:
    for det in detalles:
        producto_id = getattr(det, "producto_id", None) or det.get("producto_id")
        if not producto_id:
            continue
        prod = await get_producto_by_id(
            client_id=client_id,
            producto_id=producto_id,
            empresa_id=empresa_id,
        )
        if not prod:
            raise NotFoundError(detail="Producto no encontrado")


def _assert_editable_estado(row: dict) -> None:
    estado_actual = (row.get("estado") or "").lower()
    if estado_actual in ("ajustado", "anulado"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede editar un inventario físico en estado '{row.get('estado')}'",
        )


async def list_inventarios_fisicos_servicio(
    client_id: UUID,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[InventarioFisicoRead]:
    empresa_id = require_session_empresa_id()
    await _validate_optional_list_filtros(
        client_id, empresa_id, almacen_id=almacen_id
    )
    rows = await list_inventarios_fisicos(
        client_id=client_id,
        empresa_id=empresa_id,
        almacen_id=almacen_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return [_row_to_read(r) for r in rows]


async def get_inventario_fisico_servicio(
    client_id: UUID,
    inventario_fisico_id: UUID,
) -> InventarioFisicoRead:
    empresa_id = require_session_empresa_id()
    row = await get_inventario_fisico_by_id(
        client_id=client_id,
        inventario_fisico_id=inventario_fisico_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Inventario físico no encontrado")
    return _row_to_read(row)


async def create_inventario_fisico_servicio(
    client_id: UUID,
    data: InventarioFisicoCreate,
) -> InventarioFisicoRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    await _validate_cabecera_refs(
        client_id, empresa_id, almacen_id=data.almacen_id
    )
    payload = data.model_dump()
    payload["empresa_id"] = empresa_id
    row = await create_inventario_fisico(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_inventario_fisico_servicio(
    client_id: UUID,
    inventario_fisico_id: UUID,
    data: InventarioFisicoUpdate,
) -> InventarioFisicoRead:
    empresa_id = require_session_empresa_id()
    row = await get_inventario_fisico_by_id(
        client_id=client_id,
        inventario_fisico_id=inventario_fisico_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Inventario físico no encontrado")
    _assert_editable_estado(row)
    if data.empresa_id is not None:
        enforce_body_empresa_matches_session(data.empresa_id)
    if data.almacen_id is not None:
        await _validate_cabecera_refs(
            client_id, empresa_id, almacen_id=data.almacen_id
        )
    payload = data.model_dump(exclude_unset=True)
    if "empresa_id" in payload:
        del payload["empresa_id"]
    updated = await update_inventario_fisico(
        client_id=client_id,
        inventario_fisico_id=inventario_fisico_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)


async def anular_inventario_fisico_servicio(
    *,
    client_id: UUID,
    inventario_fisico_id: UUID,
) -> InventarioFisicoRead:
    empresa_id = require_session_empresa_id()
    row = await get_inventario_fisico_by_id(
        client_id=client_id,
        inventario_fisico_id=inventario_fisico_id,
        empresa_id=empresa_id,
    )
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
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)


async def finalizar_inventario_fisico_servicio(
    *,
    client_id: UUID,
    inventario_fisico_id: UUID,
) -> InventarioFisicoRead:
    empresa_id = require_session_empresa_id()
    row = await get_inventario_fisico_by_id(
        client_id=client_id,
        inventario_fisico_id=inventario_fisico_id,
        empresa_id=empresa_id,
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
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)


async def get_inventario_fisico_con_detalles_servicio(
    client_id: UUID,
    inventario_fisico_id: UUID,
) -> InventarioFisicoConDetalleRead:
    empresa_id = require_session_empresa_id()
    combined = await get_inventario_fisico_con_detalles(
        client_id=client_id,
        inventario_fisico_id=inventario_fisico_id,
        empresa_id=empresa_id,
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
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    await _validate_cabecera_refs(
        client_id, empresa_id, almacen_id=data.almacen_id
    )
    detalles_data = data.detalles
    if detalles_data:
        await _validate_detalle_productos(client_id, empresa_id, detalles_data)

    cab_payload = data.model_dump(exclude={"detalles"})
    now = datetime.utcnow()
    inventario_fisico_id = uuid4()

    cab_payload.update(
        inventario_fisico_id=inventario_fisico_id,
        cliente_id=client_id,
        empresa_id=empresa_id,
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
                    InvInventarioFisicoTable.c.empresa_id == empresa_id,
                    InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
        )
        det_rows = await uow.execute(
            select(InvInventarioFisicoDetalleTable)
            .where(
                and_(
                    InvInventarioFisicoDetalleTable.c.cliente_id == client_id,
                    InvInventarioFisicoDetalleTable.c.empresa_id == empresa_id,
                    InvInventarioFisicoDetalleTable.c.inventario_fisico_id
                    == inventario_fisico_id,
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
    empresa_id = require_session_empresa_id()
    row = await get_inventario_fisico_by_id(
        client_id=client_id,
        inventario_fisico_id=inventario_fisico_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Inventario físico no encontrado")
    _assert_editable_estado(row)

    if data.empresa_id is not None:
        enforce_body_empresa_matches_session(data.empresa_id)
    if data.almacen_id is not None:
        await _validate_cabecera_refs(
            client_id, empresa_id, almacen_id=data.almacen_id
        )

    cab_payload = data.model_dump(exclude_unset=True, exclude={"detalles"})
    if "empresa_id" in cab_payload:
        del cab_payload["empresa_id"]
    now = datetime.utcnow()
    detalles_data = data.detalles

    if detalles_data is not None:
        await _validate_detalle_productos(client_id, empresa_id, detalles_data)

    async with unit_of_work(client_id=client_id) as uow:
        if detalles_data is not None:
            await uow.execute(
                delete(InvInventarioFisicoDetalleTable).where(
                    and_(
                        InvInventarioFisicoDetalleTable.c.cliente_id == client_id,
                        InvInventarioFisicoDetalleTable.c.empresa_id == empresa_id,
                        InvInventarioFisicoDetalleTable.c.inventario_fisico_id
                        == inventario_fisico_id,
                    )
                )
            )
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
                k: v
                for k, v in cab_payload.items()
                if k in _INV_COLUMNS
                and k not in ("inventario_fisico_id", "cliente_id", "empresa_id")
            }
            if filtered:
                await uow.execute(
                    update(InvInventarioFisicoTable)
                    .where(
                        and_(
                            InvInventarioFisicoTable.c.cliente_id == client_id,
                            InvInventarioFisicoTable.c.empresa_id == empresa_id,
                            InvInventarioFisicoTable.c.inventario_fisico_id
                            == inventario_fisico_id,
                        )
                    )
                    .values(**filtered)
                )

        cab_rows = await uow.execute(
            select(InvInventarioFisicoTable).where(
                and_(
                    InvInventarioFisicoTable.c.cliente_id == client_id,
                    InvInventarioFisicoTable.c.empresa_id == empresa_id,
                    InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
                )
            )
        )
        det_rows = await uow.execute(
            select(InvInventarioFisicoDetalleTable)
            .where(
                and_(
                    InvInventarioFisicoDetalleTable.c.cliente_id == client_id,
                    InvInventarioFisicoDetalleTable.c.empresa_id == empresa_id,
                    InvInventarioFisicoDetalleTable.c.inventario_fisico_id
                    == inventario_fisico_id,
                )
            )
            .order_by(InvInventarioFisicoDetalleTable.c.producto_id)
        )

    cab = cab_rows[0] if cab_rows else {}
    return InventarioFisicoConDetalleRead(
        **cab,
        detalles=[_inv_det_row_to_read(d) for d in det_rows],
    )
