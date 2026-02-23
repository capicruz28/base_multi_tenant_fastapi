"""Endpoints bdg presupuesto (cabecera)."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.bdg.application.services import (
    list_presupuesto,
    get_presupuesto_by_id,
    create_presupuesto,
    update_presupuesto,
)
from app.modules.bdg.presentation.schemas import (
    PresupuestoCreate,
    PresupuestoUpdate,
    PresupuestoRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PresupuestoRead])
async def get_presupuestos(
    empresa_id: Optional[UUID] = Query(None),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    tipo_presupuesto: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_presupuesto(
        current_user.cliente_id,
        empresa_id=empresa_id,
        anio=anio,
        tipo_presupuesto=tipo_presupuesto,
        estado=estado,
        buscar=buscar,
    )


@router.get("/{presupuesto_id}", response_model=PresupuestoRead)
async def get_presupuesto(
    presupuesto_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_presupuesto_by_id(current_user.cliente_id, presupuesto_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PresupuestoRead, status_code=status.HTTP_201_CREATED)
async def post_presupuesto(
    data: PresupuestoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_presupuesto(current_user.cliente_id, data)


@router.put("/{presupuesto_id}", response_model=PresupuestoRead)
async def put_presupuesto(
    presupuesto_id: UUID,
    data: PresupuestoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_presupuesto(current_user.cliente_id, presupuesto_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
