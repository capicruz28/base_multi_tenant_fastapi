"""
Endpoints FastAPI para qms_plan_inspeccion y qms_plan_inspeccion_detalle.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.qms.application.services import (
    list_planes_inspeccion,
    get_plan_inspeccion_by_id,
    create_plan_inspeccion,
    update_plan_inspeccion,
    list_plan_inspeccion_detalles,
    get_plan_inspeccion_detalle_by_id,
    create_plan_inspeccion_detalle,
    update_plan_inspeccion_detalle,
)
from app.modules.qms.presentation.schemas import (
    PlanInspeccionCreate,
    PlanInspeccionUpdate,
    PlanInspeccionRead,
    PlanInspeccionDetalleCreate,
    PlanInspeccionDetalleUpdate,
    PlanInspeccionDetalleRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PlanInspeccionRead], tags=["QMS - Planes de Inspección"])
async def get_planes_inspeccion(
    empresa_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    categoria_id: Optional[UUID] = Query(None),
    tipo_inspeccion: Optional[str] = Query(None),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista planes de inspección del tenant."""
    return await list_planes_inspeccion(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        categoria_id=categoria_id,
        tipo_inspeccion=tipo_inspeccion,
        solo_activos=solo_activos,
        buscar=buscar
    )


@router.get("/{plan_inspeccion_id}", response_model=PlanInspeccionRead, tags=["QMS - Planes de Inspección"])
async def get_plan_inspeccion(
    plan_inspeccion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un plan de inspección por id."""
    try:
        return await get_plan_inspeccion_by_id(current_user.cliente_id, plan_inspeccion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PlanInspeccionRead, status_code=status.HTTP_201_CREATED, tags=["QMS - Planes de Inspección"])
async def post_plan_inspeccion(
    data: PlanInspeccionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un plan de inspección."""
    return await create_plan_inspeccion(current_user.cliente_id, data)


@router.put("/{plan_inspeccion_id}", response_model=PlanInspeccionRead, tags=["QMS - Planes de Inspección"])
async def put_plan_inspeccion(
    plan_inspeccion_id: UUID,
    data: PlanInspeccionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un plan de inspección."""
    try:
        return await update_plan_inspeccion(current_user.cliente_id, plan_inspeccion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Detalles de Plan de Inspección
@router.get("/{plan_inspeccion_id}/detalles", response_model=List[PlanInspeccionDetalleRead], tags=["QMS - Planes de Inspección"])
async def get_plan_inspeccion_detalles(
    plan_inspeccion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista detalles de un plan de inspección."""
    return await list_plan_inspeccion_detalles(current_user.cliente_id, plan_inspeccion_id)


@router.post("/{plan_inspeccion_id}/detalles", response_model=PlanInspeccionDetalleRead, status_code=status.HTTP_201_CREATED, tags=["QMS - Planes de Inspección"])
async def post_plan_inspeccion_detalle(
    plan_inspeccion_id: UUID,
    data: PlanInspeccionDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un detalle de plan de inspección."""
    data.plan_inspeccion_id = plan_inspeccion_id
    return await create_plan_inspeccion_detalle(current_user.cliente_id, data)


@router.get("/detalles/{plan_detalle_id}", response_model=PlanInspeccionDetalleRead, tags=["QMS - Planes de Inspección"])
async def get_plan_inspeccion_detalle(
    plan_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un detalle de plan por id."""
    try:
        return await get_plan_inspeccion_detalle_by_id(current_user.cliente_id, plan_detalle_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/detalles/{plan_detalle_id}", response_model=PlanInspeccionDetalleRead, tags=["QMS - Planes de Inspección"])
async def put_plan_inspeccion_detalle(
    plan_detalle_id: UUID,
    data: PlanInspeccionDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un detalle de plan."""
    try:
        return await update_plan_inspeccion_detalle(current_user.cliente_id, plan_detalle_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
