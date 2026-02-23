"""
Servicios de aplicación para log_despacho y log_despacho_guia.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.infrastructure.database.queries.log import (
    list_despachos as _list_despachos,
    get_despacho_by_id as _get_despacho_by_id,
    create_despacho as _create_despacho,
    update_despacho as _update_despacho,
    list_despacho_guias as _list_despacho_guias,
    get_despacho_guia_by_id as _get_despacho_guia_by_id,
    create_despacho_guia as _create_despacho_guia,
    update_despacho_guia as _update_despacho_guia,
)
from app.modules.log.presentation.schemas import (
    DespachoCreate,
    DespachoUpdate,
    DespachoRead,
    DespachoGuiaCreate,
    DespachoGuiaUpdate,
    DespachoGuiaRead,
)
from app.core.exceptions import NotFoundError


async def list_despachos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    ruta_id: Optional[UUID] = None,
    vehiculo_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    buscar: Optional[str] = None
) -> List[DespachoRead]:
    """Lista despachos del tenant."""
    rows = await _list_despachos(
        client_id=client_id,
        empresa_id=empresa_id,
        estado=estado,
        ruta_id=ruta_id,
        vehiculo_id=vehiculo_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )
    return [DespachoRead(**row) for row in rows]


async def get_despacho_by_id(client_id: UUID, despacho_id: UUID) -> DespachoRead:
    """Obtiene un despacho por id. Lanza NotFoundError si no existe."""
    row = await _get_despacho_by_id(client_id, despacho_id)
    if not row:
        raise NotFoundError(f"Despacho {despacho_id} no encontrado")
    return DespachoRead(**row)


async def create_despacho(client_id: UUID, data: DespachoCreate) -> DespachoRead:
    """Crea un despacho."""
    row = await _create_despacho(client_id, data.model_dump(exclude_none=True))
    return DespachoRead(**row)


async def update_despacho(
    client_id: UUID, despacho_id: UUID, data: DespachoUpdate
) -> DespachoRead:
    """Actualiza un despacho. Lanza NotFoundError si no existe."""
    row = await _update_despacho(
        client_id, despacho_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Despacho {despacho_id} no encontrado")
    return DespachoRead(**row)


# ============================================================================
# DESPACHO-GUÍA
# ============================================================================

async def list_despacho_guias(
    client_id: UUID,
    despacho_id: Optional[UUID] = None,
    guia_remision_id: Optional[UUID] = None,
    estado_entrega: Optional[str] = None
) -> List[DespachoGuiaRead]:
    """Lista relaciones despacho-guía del tenant."""
    rows = await _list_despacho_guias(
        client_id=client_id,
        despacho_id=despacho_id,
        guia_remision_id=guia_remision_id,
        estado_entrega=estado_entrega
    )
    return [DespachoGuiaRead(**row) for row in rows]


async def get_despacho_guia_by_id(client_id: UUID, despacho_guia_id: UUID) -> DespachoGuiaRead:
    """Obtiene una relación despacho-guía por id. Lanza NotFoundError si no existe."""
    row = await _get_despacho_guia_by_id(client_id, despacho_guia_id)
    if not row:
        raise NotFoundError(f"Relación despacho-guía {despacho_guia_id} no encontrada")
    return DespachoGuiaRead(**row)


async def create_despacho_guia(client_id: UUID, data: DespachoGuiaCreate) -> DespachoGuiaRead:
    """Crea una relación despacho-guía."""
    row = await _create_despacho_guia(client_id, data.model_dump(exclude_none=True))
    return DespachoGuiaRead(**row)


async def update_despacho_guia(
    client_id: UUID, despacho_guia_id: UUID, data: DespachoGuiaUpdate
) -> DespachoGuiaRead:
    """Actualiza una relación despacho-guía. Lanza NotFoundError si no existe."""
    row = await _update_despacho_guia(
        client_id, despacho_guia_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Relación despacho-guía {despacho_guia_id} no encontrada")
    return DespachoGuiaRead(**row)
