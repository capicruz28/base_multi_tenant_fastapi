# app/modules/inv/application/services/movimiento_service.py
"""
Servicio de Movimiento (INV). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.exceptions import NotFoundError
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.inv import (
    list_movimientos,
    get_movimiento_by_id,
    create_movimiento,
    update_movimiento,
    get_moneda_by_codigo,
)
from app.modules.inv.presentation.schemas import (
    MovimientoCreate,
    MovimientoUpdate,
    MovimientoRead,
)


def _row_to_read(row: dict) -> MovimientoRead:
    return MovimientoRead(**row)

async def _resolve_moneda_id(
    *,
    client_id: UUID,
    moneda_id: Optional[UUID],
    moneda_codigo: Optional[str],
) -> UUID:
    """
    Alinea con BD: inv_movimiento.moneda_id es NOT NULL.
    Permite compatibilidad legacy: si no viene moneda_id, resuelve por código.
    """
    if moneda_id:
        return moneda_id
    codigo = (moneda_codigo or "").strip().upper() or "PEN"
    row = await get_moneda_by_codigo(client_id=client_id, codigo=codigo, solo_activos=True)
    if not row:
        from app.core.exceptions import ValidationError
        raise ValidationError(detail=f"Moneda no encontrada o inactiva: {codigo}")
    return row["moneda_id"]


async def list_movimientos_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_movimiento_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[MovimientoRead]:
    rows = await list_movimientos(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_movimiento_id=tipo_movimiento_id,
        almacen_id=almacen_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )
    return [_row_to_read(r) for r in rows]


async def get_movimiento_servicio(
    client_id: UUID,
    movimiento_id: UUID,
) -> MovimientoRead:
    row = await get_movimiento_by_id(client_id=client_id, movimiento_id=movimiento_id)
    if not row:
        raise NotFoundError(detail="Movimiento no encontrado")
    return _row_to_read(row)


async def create_movimiento_servicio(
    client_id: UUID,
    data: MovimientoCreate,
) -> MovimientoRead:
    # Validar que la empresa pertenezca al cliente
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
    payload = data.model_dump()
    payload["moneda_id"] = await _resolve_moneda_id(
        client_id=client_id,
        moneda_id=payload.get("moneda_id"),
        moneda_codigo=payload.get("moneda"),
    )
    row = await create_movimiento(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_movimiento_servicio(
    client_id: UUID,
    movimiento_id: UUID,
    data: MovimientoUpdate,
) -> MovimientoRead:
    row = await get_movimiento_by_id(client_id=client_id, movimiento_id=movimiento_id)
    if not row:
        raise NotFoundError(detail="Movimiento no encontrado")
    # Lifecycle: impedir edición si no está en borrador
    estado_actual = (row.get("estado") or "").lower()
    if estado_actual != "borrador":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede editar un movimiento que no esté en estado 'borrador'",
        )
    # Si se actualiza empresa_id, validar pertenencia
    if data.empresa_id is not None:
        await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
    payload = data.model_dump(exclude_unset=True)
    if "moneda_id" in payload or "moneda" in payload:
        payload["moneda_id"] = await _resolve_moneda_id(
            client_id=client_id,
            moneda_id=payload.get("moneda_id"),
            moneda_codigo=payload.get("moneda"),
        )
    updated = await update_movimiento(client_id=client_id, movimiento_id=movimiento_id, data=payload)
    return _row_to_read(updated)
