# app/modules/inv/application/services/inventario_fisico_service.py
"""
Servicio de Inventario Físico (INV). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.exceptions import NotFoundError
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.inv import (
    list_inventarios_fisicos,
    get_inventario_fisico_by_id,
    create_inventario_fisico,
    update_inventario_fisico,
)
from app.modules.inv.presentation.schemas import (
    InventarioFisicoCreate,
    InventarioFisicoUpdate,
    InventarioFisicoRead,
)


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
        from fastapi import HTTPException, status
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
