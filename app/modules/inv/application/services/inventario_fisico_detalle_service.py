"""
Servicio de Inventario Físico Detalle (INV). client_id siempre desde contexto, nunca desde body.
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
    list_inventarios_fisicos_detalle,
    get_inventario_fisico_detalle_by_id,
    create_inventario_fisico_detalle,
    update_inventario_fisico_detalle,
    get_inventario_fisico_by_id,
    get_producto_by_id,
)
from app.modules.inv.presentation.schemas import (
    InventarioFisicoDetalleCreate,
    InventarioFisicoDetalleUpdate,
    InventarioFisicoDetalleRead,
)


def _row_to_read(row: dict) -> InventarioFisicoDetalleRead:
    return InventarioFisicoDetalleRead(**row)


async def _require_inventario_fisico_cabecera(
    client_id: UUID,
    empresa_id: UUID,
    inventario_fisico_id: UUID,
) -> dict:
    cab = await get_inventario_fisico_by_id(
        client_id=client_id,
        inventario_fisico_id=inventario_fisico_id,
        empresa_id=empresa_id,
    )
    if not cab:
        raise NotFoundError(detail="Inventario físico no encontrado")
    return cab


def _assert_cabecera_editable(cab: dict) -> None:
    estado = (cab.get("estado") or "").lower()
    if estado in ("ajustado", "anulado"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede modificar detalle de inventario en estado '{cab.get('estado')}'",
        )


async def _validate_optional_filtros_detalle(
    client_id: UUID,
    empresa_id: UUID,
    *,
    inventario_fisico_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> None:
    if inventario_fisico_id is not None:
        await _require_inventario_fisico_cabecera(
            client_id, empresa_id, inventario_fisico_id
        )
    if producto_id is not None:
        prod = await get_producto_by_id(
            client_id=client_id,
            producto_id=producto_id,
            empresa_id=empresa_id,
        )
        if not prod:
            raise NotFoundError(detail="Producto no encontrado")


async def _validate_detalle_producto(
    client_id: UUID,
    empresa_id: UUID,
    producto_id: UUID,
) -> None:
    prod = await get_producto_by_id(
        client_id=client_id,
        producto_id=producto_id,
        empresa_id=empresa_id,
    )
    if not prod:
        raise NotFoundError(detail="Producto no encontrado")


async def list_inventarios_fisicos_detalle_servicio(
    client_id: UUID,
    inventario_fisico_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[InventarioFisicoDetalleRead]:
    empresa_id = require_session_empresa_id()
    await _validate_optional_filtros_detalle(
        client_id,
        empresa_id,
        inventario_fisico_id=inventario_fisico_id,
        producto_id=producto_id,
    )
    rows = await list_inventarios_fisicos_detalle(
        client_id=client_id,
        empresa_id=empresa_id,
        inventario_fisico_id=inventario_fisico_id,
        producto_id=producto_id,
    )
    return [_row_to_read(r) for r in rows]


async def get_inventario_fisico_detalle_servicio(
    client_id: UUID,
    inventario_fisico_detalle_id: UUID,
) -> InventarioFisicoDetalleRead:
    empresa_id = require_session_empresa_id()
    row = await get_inventario_fisico_detalle_by_id(
        client_id=client_id,
        inventario_fisico_detalle_id=inventario_fisico_detalle_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Detalle de inventario físico no encontrado")
    return _row_to_read(row)


async def create_inventario_fisico_detalle_servicio(
    client_id: UUID,
    data: InventarioFisicoDetalleCreate,
) -> InventarioFisicoDetalleRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    cab = await _require_inventario_fisico_cabecera(
        client_id, empresa_id, data.inventario_fisico_id
    )
    _assert_cabecera_editable(cab)
    await _validate_detalle_producto(
        client_id, empresa_id, data.producto_id
    )
    payload = data.model_dump()
    payload["empresa_id"] = empresa_id
    row = await create_inventario_fisico_detalle(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_inventario_fisico_detalle_servicio(
    client_id: UUID,
    inventario_fisico_detalle_id: UUID,
    data: InventarioFisicoDetalleUpdate,
) -> InventarioFisicoDetalleRead:
    empresa_id = require_session_empresa_id()
    row = await get_inventario_fisico_detalle_by_id(
        client_id=client_id,
        inventario_fisico_detalle_id=inventario_fisico_detalle_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Detalle de inventario físico no encontrado")

    inv_id = row.get("inventario_fisico_id")
    if inv_id:
        cab = await _require_inventario_fisico_cabecera(client_id, empresa_id, inv_id)
        _assert_cabecera_editable(cab)

    payload = data.model_dump(exclude_unset=True)
    if "producto_id" in payload:
        await _validate_detalle_producto(
            client_id, empresa_id, payload["producto_id"]
        )
    updated = await update_inventario_fisico_detalle(
        client_id=client_id,
        inventario_fisico_detalle_id=inventario_fisico_detalle_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)
