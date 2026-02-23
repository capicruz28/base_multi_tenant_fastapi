"""
Endpoints FastAPI para wms_ubicacion.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.wms.application.services import (
    list_ubicaciones,
    get_ubicacion_by_id,
    create_ubicacion,
    update_ubicacion,
)
from app.modules.wms.presentation.schemas import (
    UbicacionCreate,
    UbicacionUpdate,
    UbicacionRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[UbicacionRead], tags=["WMS - Ubicaciones"])
async def get_ubicaciones(
    almacen_id: Optional[UUID] = Query(None),
    zona_id: Optional[UUID] = Query(None),
    tipo_ubicacion: Optional[str] = Query(None),
    estado_ubicacion: Optional[str] = Query(None),
    es_ubicacion_picking: Optional[bool] = Query(None),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista ubicaciones del tenant."""
    return await list_ubicaciones(
        client_id=current_user.cliente_id,
        almacen_id=almacen_id,
        zona_id=zona_id,
        tipo_ubicacion=tipo_ubicacion,
        estado_ubicacion=estado_ubicacion,
        es_ubicacion_picking=es_ubicacion_picking,
        solo_activos=solo_activos,
        buscar=buscar
    )


@router.get("/{ubicacion_id}", response_model=UbicacionRead, tags=["WMS - Ubicaciones"])
async def get_ubicacion(
    ubicacion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una ubicación por id."""
    try:
        return await get_ubicacion_by_id(current_user.cliente_id, ubicacion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=UbicacionRead, status_code=status.HTTP_201_CREATED, tags=["WMS - Ubicaciones"])
async def post_ubicacion(
    data: UbicacionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una ubicación."""
    return await create_ubicacion(current_user.cliente_id, data)


@router.put("/{ubicacion_id}", response_model=UbicacionRead, tags=["WMS - Ubicaciones"])
async def put_ubicacion(
    ubicacion_id: UUID,
    data: UbicacionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una ubicación."""
    try:
        return await update_ubicacion(current_user.cliente_id, ubicacion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
