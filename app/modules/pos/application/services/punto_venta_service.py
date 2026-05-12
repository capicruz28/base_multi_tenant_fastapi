"""
Servicios de aplicación para pos_punto_venta.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.pos import (
    list_puntos_venta as _list_puntos_venta,
    get_punto_venta_by_id as _get_punto_venta_by_id,
    create_punto_venta as _create_punto_venta,
    update_punto_venta as _update_punto_venta,
    set_punto_venta_activo as _set_punto_venta_activo,
)
from app.modules.pos.presentation.schemas import (
    PuntoVentaCreate,
    PuntoVentaUpdate,
    PuntoVentaRead,
)
from app.core.exceptions import NotFoundError


async def list_puntos_venta(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    sucursal_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[PuntoVentaRead]:
    """Lista puntos de venta del tenant."""
    rows = await _list_puntos_venta(
        client_id=client_id,
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        estado=estado,
        es_activo=es_activo,
        buscar=buscar,
    )
    return [PuntoVentaRead(**row) for row in rows]


async def get_punto_venta_by_id(
    client_id: UUID,
    punto_venta_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> PuntoVentaRead:
    """Obtiene un punto de venta por id."""
    row = await _get_punto_venta_by_id(client_id, punto_venta_id, empresa_id=empresa_id)
    if not row:
        raise NotFoundError(f"Punto de venta {punto_venta_id} no encontrado")
    return PuntoVentaRead(**row)


async def create_punto_venta(client_id: UUID, data: PuntoVentaCreate) -> PuntoVentaRead:
    """Crea un punto de venta."""
    row = await _create_punto_venta(client_id, data.model_dump(exclude_none=True))
    return PuntoVentaRead(**row)


async def update_punto_venta(
    client_id: UUID,
    punto_venta_id: UUID,
    data: PuntoVentaUpdate,
    empresa_id: Optional[UUID] = None,
) -> PuntoVentaRead:
    """Actualiza un punto de venta."""
    row = await _update_punto_venta(
        client_id,
        punto_venta_id,
        data.model_dump(exclude_none=True),
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(f"Punto de venta {punto_venta_id} no encontrado")
    return PuntoVentaRead(**row)


async def delete_punto_venta_logico(
    client_id: UUID,
    punto_venta_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> None:
    """Baja lógica (es_activo = 0)."""
    row = await _set_punto_venta_activo(
        client_id, punto_venta_id, False, empresa_id=empresa_id
    )
    if not row:
        raise NotFoundError(f"Punto de venta {punto_venta_id} no encontrado")


async def reactivar_punto_venta(
    client_id: UUID,
    punto_venta_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> PuntoVentaRead:
    """Reactiva un punto de venta (es_activo = 1)."""
    row = await _set_punto_venta_activo(
        client_id, punto_venta_id, True, empresa_id=empresa_id
    )
    if not row:
        raise NotFoundError(f"Punto de venta {punto_venta_id} no encontrado")
    return PuntoVentaRead(**row)
