"""Endpoints FastAPI para hcm_prestamo."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.hcm.application.services import (
    list_prestamos,
    get_prestamo_by_id,
    create_prestamo,
    update_prestamo,
)
from app.modules.hcm.presentation.schemas import PrestamoCreate, PrestamoUpdate, PrestamoRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PrestamoRead], tags=["HCM - Préstamos"])
async def get_prestamos(
    empresa_id: Optional[UUID] = Query(None),
    empleado_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_prestamos(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        empleado_id=empleado_id,
        estado=estado,
    )


@router.get("/{prestamo_id}", response_model=PrestamoRead, tags=["HCM - Préstamos"])
async def get_prestamo(
    prestamo_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_prestamo_by_id(current_user.cliente_id, prestamo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PrestamoRead, status_code=status.HTTP_201_CREATED, tags=["HCM - Préstamos"])
async def post_prestamo(
    data: PrestamoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_prestamo(current_user.cliente_id, data)


@router.put("/{prestamo_id}", response_model=PrestamoRead, tags=["HCM - Préstamos"])
async def put_prestamo(
    prestamo_id: UUID,
    data: PrestamoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_prestamo(current_user.cliente_id, prestamo_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
