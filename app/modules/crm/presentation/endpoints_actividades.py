"""
Endpoints FastAPI para crm_actividad.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.crm.application.services import (
    list_actividades,
    get_actividad_by_id,
    create_actividad,
    update_actividad,
)
from app.modules.crm.presentation.schemas import (
    ActividadCreate,
    ActividadUpdate,
    ActividadRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ActividadRead], tags=["CRM - Actividades"])
async def get_actividades(
    empresa_id: Optional[UUID] = Query(None),
    lead_id: Optional[UUID] = Query(None),
    oportunidad_id: Optional[UUID] = Query(None),
    cliente_venta_id: Optional[UUID] = Query(None),
    tipo_actividad: Optional[str] = Query(None),
    usuario_responsable_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista actividades del tenant."""
    return await list_actividades(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        lead_id=lead_id,
        oportunidad_id=oportunidad_id,
        cliente_venta_id=cliente_venta_id,
        tipo_actividad=tipo_actividad,
        usuario_responsable_id=usuario_responsable_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )


@router.get("/{actividad_id}", response_model=ActividadRead, tags=["CRM - Actividades"])
async def get_actividad(
    actividad_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una actividad por id."""
    try:
        return await get_actividad_by_id(current_user.cliente_id, actividad_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ActividadRead, status_code=status.HTTP_201_CREATED, tags=["CRM - Actividades"])
async def post_actividad(
    data: ActividadCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una actividad."""
    return await create_actividad(current_user.cliente_id, data)


@router.put("/{actividad_id}", response_model=ActividadRead, tags=["CRM - Actividades"])
async def put_actividad(
    actividad_id: UUID,
    data: ActividadUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una actividad."""
    try:
        return await update_actividad(current_user.cliente_id, actividad_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
