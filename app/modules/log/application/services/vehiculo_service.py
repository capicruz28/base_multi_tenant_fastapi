"""
Servicios de aplicación para log_vehiculo.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.log import (
    list_vehiculos as _list_vehiculos,
    get_vehiculo_by_id as _get_vehiculo_by_id,
    create_vehiculo as _create_vehiculo,
    update_vehiculo as _update_vehiculo,
)
from app.modules.log.presentation.schemas import (
    VehiculoCreate,
    VehiculoUpdate,
    VehiculoRead,
)
from app.core.exceptions import NotFoundError


async def list_vehiculos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    transportista_id: Optional[UUID] = None,
    tipo_propiedad: Optional[str] = None,
    estado_vehiculo: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[VehiculoRead]:
    """Lista vehículos del tenant."""
    rows = await _list_vehiculos(
        client_id=client_id,
        empresa_id=empresa_id,
        transportista_id=transportista_id,
        tipo_propiedad=tipo_propiedad,
        estado_vehiculo=estado_vehiculo,
        solo_activos=solo_activos,
        buscar=buscar
    )
    return [VehiculoRead(**row) for row in rows]


async def get_vehiculo_by_id(client_id: UUID, vehiculo_id: UUID) -> VehiculoRead:
    """Obtiene un vehículo por id. Lanza NotFoundError si no existe."""
    row = await _get_vehiculo_by_id(client_id, vehiculo_id)
    if not row:
        raise NotFoundError(f"Vehículo {vehiculo_id} no encontrado")
    return VehiculoRead(**row)


async def create_vehiculo(client_id: UUID, data: VehiculoCreate) -> VehiculoRead:
    """Crea un vehículo."""
    row = await _create_vehiculo(client_id, data.model_dump(exclude_none=True))
    return VehiculoRead(**row)


async def update_vehiculo(
    client_id: UUID, vehiculo_id: UUID, data: VehiculoUpdate
) -> VehiculoRead:
    """Actualiza un vehículo. Lanza NotFoundError si no existe."""
    row = await _update_vehiculo(
        client_id, vehiculo_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Vehículo {vehiculo_id} no encontrado")
    return VehiculoRead(**row)
