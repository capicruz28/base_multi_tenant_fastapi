"""Endpoints FastAPI para hcm_empleado."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.hcm.application.services import (
    list_empleados,
    get_empleado_by_id,
    create_empleado,
    update_empleado,
)
from app.modules.hcm.presentation.schemas import EmpleadoCreate, EmpleadoUpdate, EmpleadoRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[EmpleadoRead], tags=["HCM - Empleados"])
async def get_empleados(
    empresa_id: Optional[UUID] = Query(None),
    estado_empleado: Optional[str] = Query(None),
    es_activo: Optional[bool] = Query(None),
    departamento_id: Optional[UUID] = Query(None),
    cargo_id: Optional[UUID] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_empleados(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        estado_empleado=estado_empleado,
        es_activo=es_activo,
        departamento_id=departamento_id,
        cargo_id=cargo_id,
        buscar=buscar,
    )


@router.get("/{empleado_id}", response_model=EmpleadoRead, tags=["HCM - Empleados"])
async def get_empleado(
    empleado_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_empleado_by_id(current_user.cliente_id, empleado_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=EmpleadoRead, status_code=status.HTTP_201_CREATED, tags=["HCM - Empleados"])
async def post_empleado(
    data: EmpleadoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_empleado(current_user.cliente_id, data)


@router.put("/{empleado_id}", response_model=EmpleadoRead, tags=["HCM - Empleados"])
async def put_empleado(
    empleado_id: UUID,
    data: EmpleadoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_empleado(current_user.cliente_id, empleado_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
