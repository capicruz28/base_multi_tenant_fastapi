"""Endpoints FastAPI para hcm_vacaciones."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.hcm.application.services import (
    list_vacaciones,
    get_vacaciones_by_id,
    create_vacaciones,
    update_vacaciones,
)
from app.modules.hcm.presentation.schemas import VacacionesCreate, VacacionesUpdate, VacacionesRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[VacacionesRead], tags=["HCM - Vacaciones"])
async def get_vacaciones(
    empresa_id: Optional[UUID] = Query(None),
    empleado_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    año_periodo: Optional[int] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_vacaciones(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        empleado_id=empleado_id,
        estado=estado,
        año_periodo=año_periodo,
    )


@router.get("/{vacaciones_id}", response_model=VacacionesRead, tags=["HCM - Vacaciones"])
async def get_vacaciones_by_id_endpoint(
    vacaciones_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_vacaciones_by_id(current_user.cliente_id, vacaciones_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=VacacionesRead, status_code=status.HTTP_201_CREATED, tags=["HCM - Vacaciones"])
async def post_vacaciones(
    data: VacacionesCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_vacaciones(current_user.cliente_id, data)


@router.put("/{vacaciones_id}", response_model=VacacionesRead, tags=["HCM - Vacaciones"])
async def put_vacaciones(
    vacaciones_id: UUID,
    data: VacacionesUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_vacaciones(current_user.cliente_id, vacaciones_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
