"""Endpoints mnt_historial_mantenimiento."""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
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

MODULE_CODE = "mnt"
RESOURCE_CODE = "historial_mantenimiento"

router = APIRouter()


@router.get("", response_model=List[HistorialMantenimientoRead], tags=["MNT - Historial Mantenimiento"])
async def get_historiales_mantenimiento(
    activo_id: Optional[UUID] = Query(None),
    orden_trabajo_id: Optional[UUID] = Query(None),
    tipo_mantenimiento: Optional[str] = Query(None),
    empresa_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[date] = Query(None, description="Filtra historial con fecha_mantenimiento >= fecha_desde"),
    fecha_hasta: Optional[date] = Query(None, description="Filtra historial con fecha_mantenimiento <= fecha_hasta"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    return await list_historial_mantenimiento(
        current_user.cliente_id,
        activo_id=activo_id,
        orden_trabajo_id=orden_trabajo_id,
        tipo_mantenimiento=tipo_mantenimiento,
        empresa_id=empresa_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.get("/{historial_id}", response_model=HistorialMantenimientoRead, tags=["MNT - Historial Mantenimiento"])
async def get_historial_mantenimiento(
    historial_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    try:
        return await get_historial_mantenimiento_by_id(current_user.cliente_id, historial_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=HistorialMantenimientoRead, status_code=status.HTTP_201_CREATED, tags=["MNT - Historial Mantenimiento"])
async def post_historial_mantenimiento(
    data: HistorialMantenimientoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    return await create_historial_mantenimiento(current_user.cliente_id, data)


@router.put("/{historial_id}", response_model=HistorialMantenimientoRead, tags=["MNT - Historial Mantenimiento"])
async def put_historial_mantenimiento(
    historial_id: UUID,
    data: HistorialMantenimientoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    try:
        return await update_historial_mantenimiento(current_user.cliente_id, historial_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
