# app/modules/pur/application/services/contacto_service.py
"""
Servicio de Contacto de Proveedor (PUR). client_id siempre desde contexto, nunca desde body.
"""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.pur import (
    list_contactos,
    get_contacto_by_id,
    create_contacto,
    update_contacto,
)
from app.modules.pur.presentation.schemas import (
    ContactoProveedorCreate,
    ContactoProveedorUpdate,
    ContactoProveedorRead,
)


def _row_to_read(row: dict) -> ContactoProveedorRead:
    return ContactoProveedorRead(**row)


async def list_contactos_servicio(
    client_id: UUID,
    proveedor_id: Optional[UUID] = None,
    solo_activos: bool = True,
) -> List[ContactoProveedorRead]:
    rows = await list_contactos(
        client_id=client_id,
        proveedor_id=proveedor_id,
        solo_activos=solo_activos
    )
    return [_row_to_read(r) for r in rows]


async def get_contacto_servicio(
    client_id: UUID,
    contacto_id: UUID,
) -> ContactoProveedorRead:
    row = await get_contacto_by_id(client_id=client_id, contacto_id=contacto_id)
    if not row:
        raise NotFoundError(detail="Contacto no encontrado")
    return _row_to_read(row)


async def create_contacto_servicio(
    client_id: UUID,
    data: ContactoProveedorCreate,
) -> ContactoProveedorRead:
    payload = data.model_dump()
    row = await create_contacto(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_contacto_servicio(
    client_id: UUID,
    contacto_id: UUID,
    data: ContactoProveedorUpdate,
) -> ContactoProveedorRead:
    row = await get_contacto_by_id(client_id=client_id, contacto_id=contacto_id)
    if not row:
        raise NotFoundError(detail="Contacto no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_contacto(client_id=client_id, contacto_id=contacto_id, data=payload)
    return _row_to_read(updated)
