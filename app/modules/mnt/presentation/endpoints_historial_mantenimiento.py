"""Endpoints mnt_historial_mantenimiento."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mnt.application.services import (
    list_historial_mantenimiento,
    get_historial_mantenimiento_by_id,
    create_historial_mantenimiento,
    update_historial_mantenimiento,
)
from app.modules.mnt.presentation.schemas import (
    HistorialMantenimientoCreate,
    HistorialMantenimientoUpdate,
    HistorialMantenimientoRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[HistorialMantenimientoRead], tags=["MNT - Historial Mantenimiento"])
async def get_historiales_mantenimiento(
    activo_id: Optional[UUID] = Query(None),
    orden_trabajo_id: Optional[UUID] = Query(None),
    tipo_mantenimiento: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_historial_mantenimiento(
        current_user.cliente_id,
        activo_id=activo_id,
        orden_trabajo_id=orden_trabajo_id,
        tipo_mantenimiento=tipo_mantenimiento,
    )


@router.get("/{historial_id}", response_model=HistorialMantenimientoRead, tags=["MNT - Historial Mantenimiento"])
async def get_historial_mantenimiento(
    historial_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_historial_mantenimiento_by_id(current_user.cliente_id, historial_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=HistorialMantenimientoRead, status_code=status.HTTP_201_CREATED, tags=["MNT - Historial Mantenimiento"])
async def post_historial_mantenimiento(
    data: HistorialMantenimientoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_historial_mantenimiento(current_user.cliente_id, data)


@router.put("/{historial_id}", response_model=HistorialMantenimientoRead, tags=["MNT - Historial Mantenimiento"])
async def put_historial_mantenimiento(
    historial_id: UUID,
    data: HistorialMantenimientoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_historial_mantenimiento(current_user.cliente_id, historial_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
