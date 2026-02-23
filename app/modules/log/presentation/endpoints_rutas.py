"""
Endpoints FastAPI para log_ruta.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.log.application.services import (
    list_rutas,
    get_ruta_by_id,
    create_ruta,
    update_ruta,
)
from app.modules.log.presentation.schemas import (
    RutaCreate,
    RutaUpdate,
    RutaRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[RutaRead], tags=["LOG - Rutas"])
async def get_rutas(
    empresa_id: Optional[UUID] = Query(None),
    origen_sucursal_id: Optional[UUID] = Query(None),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista rutas del tenant."""
    return await list_rutas(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        origen_sucursal_id=origen_sucursal_id,
        solo_activos=solo_activos,
        buscar=buscar
    )


@router.get("/{ruta_id}", response_model=RutaRead, tags=["LOG - Rutas"])
async def get_ruta(
    ruta_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una ruta por id."""
    try:
        return await get_ruta_by_id(current_user.cliente_id, ruta_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=RutaRead, status_code=status.HTTP_201_CREATED, tags=["LOG - Rutas"])
async def post_ruta(
    data: RutaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una ruta."""
    return await create_ruta(current_user.cliente_id, data)


@router.put("/{ruta_id}", response_model=RutaRead, tags=["LOG - Rutas"])
async def put_ruta(
    ruta_id: UUID,
    data: RutaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una ruta."""
    try:
        return await update_ruta(current_user.cliente_id, ruta_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
