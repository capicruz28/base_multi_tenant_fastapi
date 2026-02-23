"""
Endpoints FastAPI para qms_parametro_calidad.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.qms.application.services import (
    list_parametros_calidad,
    get_parametro_calidad_by_id,
    create_parametro_calidad,
    update_parametro_calidad,
)
from app.modules.qms.presentation.schemas import (
    ParametroCalidadCreate,
    ParametroCalidadUpdate,
    ParametroCalidadRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ParametroCalidadRead], tags=["QMS - Parámetros de Calidad"])
async def get_parametros_calidad(
    empresa_id: Optional[UUID] = Query(None),
    tipo_parametro: Optional[str] = Query(None),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista parámetros de calidad del tenant."""
    return await list_parametros_calidad(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_parametro=tipo_parametro,
        solo_activos=solo_activos,
        buscar=buscar
    )


@router.get("/{parametro_id}", response_model=ParametroCalidadRead, tags=["QMS - Parámetros de Calidad"])
async def get_parametro_calidad(
    parametro_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un parámetro de calidad por id."""
    try:
        return await get_parametro_calidad_by_id(current_user.cliente_id, parametro_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ParametroCalidadRead, status_code=status.HTTP_201_CREATED, tags=["QMS - Parámetros de Calidad"])
async def post_parametro_calidad(
    data: ParametroCalidadCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un parámetro de calidad."""
    return await create_parametro_calidad(current_user.cliente_id, data)


@router.put("/{parametro_id}", response_model=ParametroCalidadRead, tags=["QMS - Parámetros de Calidad"])
async def put_parametro_calidad(
    parametro_id: UUID,
    data: ParametroCalidadUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un parámetro de calidad."""
    try:
        return await update_parametro_calidad(current_user.cliente_id, parametro_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
