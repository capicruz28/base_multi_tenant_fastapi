"""Endpoints pm proyecto."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pm.application.services import (
    list_proyecto,
    get_proyecto_by_id,
    create_proyecto,
    update_proyecto,
)
from app.modules.pm.presentation.schemas import (
    ProyectoCreate,
    ProyectoUpdate,
    ProyectoRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ProyectoRead])
async def get_proyectos(
    empresa_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    cliente_venta_id: Optional[UUID] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_proyecto(
        current_user.cliente_id,
        empresa_id=empresa_id,
        estado=estado,
        cliente_venta_id=cliente_venta_id,
        buscar=buscar,
    )


@router.get("/{proyecto_id}", response_model=ProyectoRead)
async def get_proyecto(
    proyecto_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_proyecto_by_id(current_user.cliente_id, proyecto_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ProyectoRead, status_code=status.HTTP_201_CREATED)
async def post_proyecto(
    data: ProyectoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_proyecto(current_user.cliente_id, data)


@router.put("/{proyecto_id}", response_model=ProyectoRead)
async def put_proyecto(
    proyecto_id: UUID,
    data: ProyectoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_proyecto(current_user.cliente_id, proyecto_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
