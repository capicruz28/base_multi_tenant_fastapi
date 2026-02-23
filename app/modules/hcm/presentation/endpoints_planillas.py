"""Endpoints FastAPI para hcm_planilla."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.hcm.application.services import (
    list_planillas,
    get_planilla_by_id,
    create_planilla,
    update_planilla,
)
from app.modules.hcm.presentation.schemas import PlanillaCreate, PlanillaUpdate, PlanillaRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PlanillaRead], tags=["HCM - Planillas"])
async def get_planillas(
    empresa_id: Optional[UUID] = Query(None),
    tipo_planilla: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    año: Optional[int] = Query(None),
    mes: Optional[int] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_planillas(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_planilla=tipo_planilla,
        estado=estado,
        año=año,
        mes=mes,
    )


@router.get("/{planilla_id}", response_model=PlanillaRead, tags=["HCM - Planillas"])
async def get_planilla(
    planilla_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_planilla_by_id(current_user.cliente_id, planilla_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PlanillaRead, status_code=status.HTTP_201_CREATED, tags=["HCM - Planillas"])
async def post_planilla(
    data: PlanillaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_planilla(current_user.cliente_id, data)


@router.put("/{planilla_id}", response_model=PlanillaRead, tags=["HCM - Planillas"])
async def put_planilla(
    planilla_id: UUID,
    data: PlanillaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_planilla(current_user.cliente_id, planilla_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
