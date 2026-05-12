# app/modules/pur/application/services/proveedor_service.py
"""
Servicio de Proveedor (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.pur import (
    list_proveedores,
    get_proveedor_by_id,
    create_proveedor,
    update_proveedor,
)
from app.modules.pur.presentation.schemas import (
    ProveedorCreate,
    ProveedorUpdate,
    ProveedorRead,
)


def _row_to_read(row: dict) -> ProveedorRead:
    return ProveedorRead(**row)


async def list_proveedores_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    tipo_proveedor: Optional[str] = None,
    categoria_proveedor: Optional[str] = None,
    estado: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    sort_by: Optional[str] = None,
    order: Optional[str] = None,
) -> List[ProveedorRead]:
    skip = (page - 1) * page_size if page is not None and page_size is not None else None
    limit = page_size if page_size is not None else None
    rows = await list_proveedores(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
        buscar=buscar,
        tipo_proveedor=tipo_proveedor,
        categoria_proveedor=categoria_proveedor,
        estado=estado,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order,
    )
    return [_row_to_read(r) for r in rows]


async def get_proveedor_servicio(
    client_id: UUID,
    proveedor_id: UUID,
) -> ProveedorRead:
    row = await get_proveedor_by_id(client_id=client_id, proveedor_id=proveedor_id)
    if not row:
        raise NotFoundError(detail="Proveedor no encontrado")
    return _row_to_read(row)


async def create_proveedor_servicio(
    client_id: UUID,
    data: ProveedorCreate,
) -> ProveedorRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
    payload = data.model_dump()
    row = await create_proveedor(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_proveedor_servicio(
    client_id: UUID,
    proveedor_id: UUID,
    data: ProveedorUpdate,
) -> ProveedorRead:
    row = await get_proveedor_by_id(client_id=client_id, proveedor_id=proveedor_id)
    if not row:
        raise NotFoundError(detail="Proveedor no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_proveedor(client_id=client_id, proveedor_id=proveedor_id, data=payload)
    return _row_to_read(updated)


async def reactivar_proveedor_servicio(
    client_id: UUID,
    proveedor_id: UUID,
) -> ProveedorRead:
    row = await get_proveedor_by_id(client_id=client_id, proveedor_id=proveedor_id)
    if not row:
        raise NotFoundError(detail="Proveedor no encontrado")
    updated = await update_proveedor(
        client_id=client_id,
        proveedor_id=proveedor_id,
        data={"es_activo": True, "estado": "activo"},
    )
    return _row_to_read(updated)
