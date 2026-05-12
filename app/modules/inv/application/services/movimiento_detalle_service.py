"""
Servicio de Movimiento Detalle (INV). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.inv import (
    list_movimientos_detalle,
    get_movimiento_detalle_by_id,
    create_movimiento_detalle,
    update_movimiento_detalle,
    get_moneda_by_codigo,
    get_movimiento_by_id,
)
from app.modules.inv.presentation.schemas import (
    MovimientoDetalleCreate,
    MovimientoDetalleUpdate,
    MovimientoDetalleRead,
)


def _row_to_read(row: dict) -> MovimientoDetalleRead:
    return MovimientoDetalleRead(**row)

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


async def list_movimientos_detalle_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    movimiento_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[MovimientoDetalleRead]:
    rows = await list_movimientos_detalle(
        client_id=client_id,
        empresa_id=empresa_id,
        movimiento_id=movimiento_id,
        producto_id=producto_id,
    )
    return [_row_to_read(r) for r in rows]


async def get_movimiento_detalle_servicio(
    client_id: UUID,
    movimiento_detalle_id: UUID,
) -> MovimientoDetalleRead:
    row = await get_movimiento_detalle_by_id(
        client_id=client_id, movimiento_detalle_id=movimiento_detalle_id
    )
    if not row:
        raise NotFoundError(detail="Detalle de movimiento no encontrado")
    return _row_to_read(row)


async def create_movimiento_detalle_servicio(
    client_id: UUID,
    data: MovimientoDetalleCreate,
) -> MovimientoDetalleRead:
    payload = data.model_dump()
    payload["moneda_id"] = await _resolve_moneda_id(
        client_id=client_id,
        moneda_id=payload.get("moneda_id"),
        moneda_codigo=payload.get("moneda"),
    )
    row = await create_movimiento_detalle(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_movimiento_detalle_servicio(
    client_id: UUID,
    movimiento_detalle_id: UUID,
    data: MovimientoDetalleUpdate,
) -> MovimientoDetalleRead:
    row = await get_movimiento_detalle_by_id(
        client_id=client_id, movimiento_detalle_id=movimiento_detalle_id
    )
    if not row:
        raise NotFoundError(detail="Detalle de movimiento no encontrado")
    # Lifecycle: impedir edición del detalle si la cabecera no está en borrador
    movimiento_id = row.get("movimiento_id")
    if movimiento_id:
        cab = await get_movimiento_by_id(client_id=client_id, movimiento_id=movimiento_id)
        estado_cab = (cab.get("estado") or "").lower() if cab else ""
        if estado_cab and estado_cab != "borrador":
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede editar el detalle si el movimiento no está en estado 'borrador'",
            )
    payload = data.model_dump(exclude_unset=True)
    if "moneda_id" in payload or "moneda" in payload:
        payload["moneda_id"] = await _resolve_moneda_id(
            client_id=client_id,
            moneda_id=payload.get("moneda_id"),
            moneda_codigo=payload.get("moneda"),
        )
    updated = await update_movimiento_detalle(
        client_id=client_id, movimiento_detalle_id=movimiento_detalle_id, data=payload
    )
    return _row_to_read(updated)

