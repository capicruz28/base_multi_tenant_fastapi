"""Endpoints FastAPI para hcm_planilla_empleado."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.hcm.application.services import (
    list_planilla_empleados,
    get_planilla_empleado_by_id,
    create_planilla_empleado,
    update_planilla_empleado,
)
from app.modules.hcm.presentation.schemas import PlanillaEmpleadoCreate, PlanillaEmpleadoUpdate, PlanillaEmpleadoRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PlanillaEmpleadoRead], tags=["HCM - Planilla Empleados"])
async def get_planilla_empleados(
    planilla_id: Optional[UUID] = Query(None),
    empleado_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_planilla_empleados(
        client_id=current_user.cliente_id,
        planilla_id=planilla_id,
        empleado_id=empleado_id,
    )


@router.get("/{planilla_empleado_id}", response_model=PlanillaEmpleadoRead, tags=["HCM - Planilla Empleados"])
async def get_planilla_empleado(
    planilla_empleado_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_planilla_empleado_by_id(current_user.cliente_id, planilla_empleado_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PlanillaEmpleadoRead, status_code=status.HTTP_201_CREATED, tags=["HCM - Planilla Empleados"])
async def post_planilla_empleado(
    data: PlanillaEmpleadoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_planilla_empleado(current_user.cliente_id, data)


@router.put("/{planilla_empleado_id}", response_model=PlanillaEmpleadoRead, tags=["HCM - Planilla Empleados"])
async def put_planilla_empleado(
    planilla_empleado_id: UUID,
    data: PlanillaEmpleadoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_planilla_empleado(current_user.cliente_id, planilla_empleado_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
