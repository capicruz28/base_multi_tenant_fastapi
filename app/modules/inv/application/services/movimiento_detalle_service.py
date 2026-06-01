"""
Servicio de Movimiento Detalle (INV). client_id siempre desde contexto, nunca desde body.
Aislamiento multi-empresa: empresa_id desde sesión JWT (company_scope).
"""
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.core.exceptions import NotFoundError
from app.core.tenant.company_scope import (
    require_session_empresa_id,
    enforce_body_empresa_matches_session,
)
from app.infrastructure.database.queries.inv import (
    list_movimientos_detalle,
    get_movimiento_detalle_by_id,
    create_movimiento_detalle,
    update_movimiento_detalle,
    get_moneda_by_codigo,
    get_movimiento_by_id,
    get_producto_by_id,
    get_unidad_medida_by_id,
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


async def _require_movimiento_cabecera(
    client_id: UUID,
    empresa_id: UUID,
    movimiento_id: UUID,
) -> dict:
    cab = await get_movimiento_by_id(
        client_id=client_id,
        movimiento_id=movimiento_id,
        empresa_id=empresa_id,
    )
    if not cab:
        raise NotFoundError(detail="Movimiento no encontrado")
    return cab


async def _validate_detalle_linea_refs(
    client_id: UUID,
    empresa_id: UUID,
    *,
    producto_id: UUID,
    unidad_medida_id: UUID,
) -> None:
    prod = await get_producto_by_id(
        client_id=client_id,
        producto_id=producto_id,
        empresa_id=empresa_id,
    )
    if not prod:
        raise NotFoundError(detail="Producto no encontrado")
    um = await get_unidad_medida_by_id(
        client_id=client_id,
        unidad_medida_id=unidad_medida_id,
        empresa_id=empresa_id,
    )
    if not um:
        raise NotFoundError(detail="Unidad de medida no encontrada")


async def _validate_optional_filtros_detalle(
    client_id: UUID,
    empresa_id: UUID,
    *,
    movimiento_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> None:
    if movimiento_id is not None:
        await _require_movimiento_cabecera(client_id, empresa_id, movimiento_id)
    if producto_id is not None:
        prod = await get_producto_by_id(
            client_id=client_id,
            producto_id=producto_id,
            empresa_id=empresa_id,
        )
        if not prod:
            raise NotFoundError(detail="Producto no encontrado")


async def list_movimientos_detalle_servicio(
    client_id: UUID,
    movimiento_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[MovimientoDetalleRead]:
    empresa_id = require_session_empresa_id()
    await _validate_optional_filtros_detalle(
        client_id,
        empresa_id,
        movimiento_id=movimiento_id,
        producto_id=producto_id,
    )
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
    empresa_id = require_session_empresa_id()
    row = await get_movimiento_detalle_by_id(
        client_id=client_id,
        movimiento_detalle_id=movimiento_detalle_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Detalle de movimiento no encontrado")
    return _row_to_read(row)


async def create_movimiento_detalle_servicio(
    client_id: UUID,
    data: MovimientoDetalleCreate,
) -> MovimientoDetalleRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    cab = await _require_movimiento_cabecera(
        client_id, empresa_id, data.movimiento_id
    )
    if (cab.get("estado") or "").lower() != "borrador":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede agregar detalle si el movimiento no está en estado 'borrador'",
        )
    await _validate_detalle_linea_refs(
        client_id,
        empresa_id,
        producto_id=data.producto_id,
        unidad_medida_id=data.unidad_medida_id,
    )
    payload = data.model_dump()
    payload["empresa_id"] = empresa_id
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
    empresa_id = require_session_empresa_id()
    row = await get_movimiento_detalle_by_id(
        client_id=client_id,
        movimiento_detalle_id=movimiento_detalle_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Detalle de movimiento no encontrado")

    movimiento_id = row.get("movimiento_id")
    if movimiento_id:
        cab = await _require_movimiento_cabecera(
            client_id, empresa_id, movimiento_id
        )
        estado_cab = (cab.get("estado") or "").lower()
        if estado_cab != "borrador":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede editar el detalle si el movimiento no está en estado 'borrador'",
            )

    payload = data.model_dump(exclude_unset=True)
    if "producto_id" in payload or "unidad_medida_id" in payload:
        await _validate_detalle_linea_refs(
            client_id,
            empresa_id,
            producto_id=payload.get("producto_id", row.get("producto_id")),
            unidad_medida_id=payload.get(
                "unidad_medida_id", row.get("unidad_medida_id")
            ),
        )
    if "moneda_id" in payload or "moneda" in payload:
        payload["moneda_id"] = await _resolve_moneda_id(
            client_id=client_id,
            moneda_id=payload.get("moneda_id"),
            moneda_codigo=payload.get("moneda"),
        )
    updated = await update_movimiento_detalle(
        client_id=client_id,
        movimiento_detalle_id=movimiento_detalle_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)
