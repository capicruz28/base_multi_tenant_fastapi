"""Endpoints FastAPI para hcm_asistencia."""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.hcm.application.services import (
    list_asistencias,
    get_asistencia_by_id,
    create_asistencia,
    update_asistencia,
)
from app.modules.hcm.presentation.schemas import AsistenciaCreate, AsistenciaUpdate, AsistenciaRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[AsistenciaRead], tags=["HCM - Asistencia"])
async def get_asistencias(
    empresa_id: Optional[UUID] = Query(None),
    empleado_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    tipo_asistencia: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_asistencias(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        empleado_id=empleado_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        tipo_asistencia=tipo_asistencia,
    )


@router.get("/{asistencia_id}", response_model=AsistenciaRead, tags=["HCM - Asistencia"])
async def get_asistencia(
    asistencia_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_asistencia_by_id(current_user.cliente_id, asistencia_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=AsistenciaRead, status_code=status.HTTP_201_CREATED, tags=["HCM - Asistencia"])
async def post_asistencia(
    data: AsistenciaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_asistencia(current_user.cliente_id, data)


@router.put("/{asistencia_id}", response_model=AsistenciaRead, tags=["HCM - Asistencia"])
async def put_asistencia(
    asistencia_id: UUID,
    data: AsistenciaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_asistencia(current_user.cliente_id, asistencia_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
