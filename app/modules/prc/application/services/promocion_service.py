"""
Servicios de aplicación para prc_promocion.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date

from app.infrastructure.database.queries.prc import (
    list_promociones as _list_promociones,
    get_promocion_by_id as _get_promocion_by_id,
    create_promocion as _create_promocion,
    update_promocion as _update_promocion,
)
from app.modules.prc.presentation.schemas import (
    PromocionCreate,
    PromocionUpdate,
    PromocionRead,
)
from app.core.exceptions import NotFoundError


async def list_promociones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_promocion: Optional[str] = None,
    aplica_a: Optional[str] = None,
    producto_id: Optional[UUID] = None,
    categoria_id: Optional[UUID] = None,
    solo_activos: bool = True,
    solo_vigentes: bool = False,
    buscar: Optional[str] = None
) -> List[PromocionRead]:
    """Lista promociones del tenant."""
    rows = await _list_promociones(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_promocion=tipo_promocion,
        aplica_a=aplica_a,
        producto_id=producto_id,
        categoria_id=categoria_id,
        solo_activos=solo_activos,
        solo_vigentes=solo_vigentes,
        buscar=buscar
    )
    return [PromocionRead(**row) for row in rows]


async def get_promocion_by_id(client_id: UUID, promocion_id: UUID) -> PromocionRead:
    """Obtiene una promoción por id. Lanza NotFoundError si no existe."""
    row = await _get_promocion_by_id(client_id, promocion_id)
    if not row:
        raise NotFoundError(f"Promoción {promocion_id} no encontrada")
    return PromocionRead(**row)


async def create_promocion(client_id: UUID, data: PromocionCreate) -> PromocionRead:
    """Crea una promoción."""
    row = await _create_promocion(client_id, data.model_dump(exclude_none=True))
    return PromocionRead(**row)


async def update_promocion(
    client_id: UUID, promocion_id: UUID, data: PromocionUpdate
) -> PromocionRead:
    """Actualiza una promoción. Lanza NotFoundError si no existe."""
    row = await _update_promocion(
        client_id, promocion_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Promoción {promocion_id} no encontrada")
    return PromocionRead(**row)
