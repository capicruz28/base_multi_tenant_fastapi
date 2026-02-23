"""Servicios de aplicación para hcm_prestamo."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.hcm import (
    list_prestamos as _list,
    get_prestamo_by_id as _get,
    create_prestamo as _create,
    update_prestamo as _update,
)
from app.modules.hcm.presentation.schemas import PrestamoCreate, PrestamoUpdate, PrestamoRead
from app.core.exceptions import NotFoundError


async def list_prestamos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    empleado_id: Optional[UUID] = None,
    estado: Optional[str] = None,
) -> List[PrestamoRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        empleado_id=empleado_id,
        estado=estado,
    )
    return [PrestamoRead(**r) for r in rows]


async def get_prestamo_by_id(client_id: UUID, prestamo_id: UUID) -> PrestamoRead:
    row = await _get(client_id, prestamo_id)
    if not row:
        raise NotFoundError(f"Préstamo {prestamo_id} no encontrado")
    return PrestamoRead(**row)


async def create_prestamo(client_id: UUID, data: PrestamoCreate) -> PrestamoRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return PrestamoRead(**row)


async def update_prestamo(
    client_id: UUID, prestamo_id: UUID, data: PrestamoUpdate
) -> PrestamoRead:
    row = await _update(client_id, prestamo_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Préstamo {prestamo_id} no encontrado")
    return PrestamoRead(**row)
