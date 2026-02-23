"""Endpoints FastAPI para hcm_planilla_detalle."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.hcm.application.services import (
    list_planilla_detalles,
    get_planilla_detalle_by_id,
    create_planilla_detalle,
    update_planilla_detalle,
)
from app.modules.hcm.presentation.schemas import PlanillaDetalleCreate, PlanillaDetalleUpdate, PlanillaDetalleRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PlanillaDetalleRead], tags=["HCM - Planilla Detalle"])
async def get_planilla_detalles(
    planilla_empleado_id: Optional[UUID] = Query(None),
    tipo_concepto: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_planilla_detalles(
        client_id=current_user.cliente_id,
        planilla_empleado_id=planilla_empleado_id,
        tipo_concepto=tipo_concepto,
    )


@router.get("/{planilla_detalle_id}", response_model=PlanillaDetalleRead, tags=["HCM - Planilla Detalle"])
async def get_planilla_detalle(
    planilla_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_planilla_detalle_by_id(current_user.cliente_id, planilla_detalle_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PlanillaDetalleRead, status_code=status.HTTP_201_CREATED, tags=["HCM - Planilla Detalle"])
async def post_planilla_detalle(
    data: PlanillaDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_planilla_detalle(current_user.cliente_id, data)


@router.put("/{planilla_detalle_id}", response_model=PlanillaDetalleRead, tags=["HCM - Planilla Detalle"])
async def put_planilla_detalle(
    planilla_detalle_id: UUID,
    data: PlanillaDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_planilla_detalle(current_user.cliente_id, planilla_detalle_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
