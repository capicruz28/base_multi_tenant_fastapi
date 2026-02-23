"""Endpoints mnt_orden_trabajo."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mnt.application.services import (
    list_orden_trabajo,
    get_orden_trabajo_by_id,
    create_orden_trabajo,
    update_orden_trabajo,
)
from app.modules.mnt.presentation.schemas import OrdenTrabajoCreate, OrdenTrabajoUpdate, OrdenTrabajoRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[OrdenTrabajoRead], tags=["MNT - Órdenes de Trabajo"])
async def get_ordenes_trabajo(
    empresa_id: Optional[UUID] = Query(None),
    activo_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    tipo_mantenimiento: Optional[str] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_orden_trabajo(
        current_user.cliente_id,
        empresa_id=empresa_id,
        activo_id=activo_id,
        estado=estado,
        tipo_mantenimiento=tipo_mantenimiento,
        buscar=buscar,
    )


@router.get("/{orden_trabajo_id}", response_model=OrdenTrabajoRead, tags=["MNT - Órdenes de Trabajo"])
async def get_orden_trabajo(
    orden_trabajo_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_orden_trabajo_by_id(current_user.cliente_id, orden_trabajo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=OrdenTrabajoRead, status_code=status.HTTP_201_CREATED, tags=["MNT - Órdenes de Trabajo"])
async def post_orden_trabajo(
    data: OrdenTrabajoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_orden_trabajo(current_user.cliente_id, data)


@router.put("/{orden_trabajo_id}", response_model=OrdenTrabajoRead, tags=["MNT - Órdenes de Trabajo"])
async def put_orden_trabajo(
    orden_trabajo_id: UUID,
    data: OrdenTrabajoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_orden_trabajo(current_user.cliente_id, orden_trabajo_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
