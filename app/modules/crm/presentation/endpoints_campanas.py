"""
Endpoints FastAPI para crm_campana.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.crm.application.services import (
    list_campanas,
    get_campana_by_id,
    create_campana,
    update_campana,
)
from app.modules.crm.presentation.schemas import (
    CampanaCreate,
    CampanaUpdate,
    CampanaRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[CampanaRead], tags=["CRM - Campañas"])
async def get_campanas(
    empresa_id: Optional[UUID] = Query(None),
    tipo_campana: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista campañas del tenant."""
    return await list_campanas(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_campana=tipo_campana,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )


@router.get("/{campana_id}", response_model=CampanaRead, tags=["CRM - Campañas"])
async def get_campana(
    campana_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una campaña por id."""
    try:
        return await get_campana_by_id(current_user.cliente_id, campana_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=CampanaRead, status_code=status.HTTP_201_CREATED, tags=["CRM - Campañas"])
async def post_campana(
    data: CampanaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una campaña."""
    return await create_campana(current_user.cliente_id, data)


@router.put("/{campana_id}", response_model=CampanaRead, tags=["CRM - Campañas"])
async def put_campana(
    campana_id: UUID,
    data: CampanaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una campaña."""
    try:
        return await update_campana(current_user.cliente_id, campana_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
