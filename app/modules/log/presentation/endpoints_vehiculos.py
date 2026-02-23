"""
Endpoints FastAPI para log_vehiculo.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.log.application.services import (
    list_vehiculos,
    get_vehiculo_by_id,
    create_vehiculo,
    update_vehiculo,
)
from app.modules.log.presentation.schemas import (
    VehiculoCreate,
    VehiculoUpdate,
    VehiculoRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[VehiculoRead], tags=["LOG - Vehículos"])
async def get_vehiculos(
    empresa_id: Optional[UUID] = Query(None),
    transportista_id: Optional[UUID] = Query(None),
    tipo_propiedad: Optional[str] = Query(None),
    estado_vehiculo: Optional[str] = Query(None),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista vehículos del tenant."""
    return await list_vehiculos(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        transportista_id=transportista_id,
        tipo_propiedad=tipo_propiedad,
        estado_vehiculo=estado_vehiculo,
        solo_activos=solo_activos,
        buscar=buscar
    )


@router.get("/{vehiculo_id}", response_model=VehiculoRead, tags=["LOG - Vehículos"])
async def get_vehiculo(
    vehiculo_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un vehículo por id."""
    try:
        return await get_vehiculo_by_id(current_user.cliente_id, vehiculo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=VehiculoRead, status_code=status.HTTP_201_CREATED, tags=["LOG - Vehículos"])
async def post_vehiculo(
    data: VehiculoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un vehículo."""
    return await create_vehiculo(current_user.cliente_id, data)


@router.put("/{vehiculo_id}", response_model=VehiculoRead, tags=["LOG - Vehículos"])
async def put_vehiculo(
    vehiculo_id: UUID,
    data: VehiculoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un vehículo."""
    try:
        return await update_vehiculo(current_user.cliente_id, vehiculo_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
