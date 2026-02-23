"""
Endpoints FastAPI para crm_lead.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.crm.application.services import (
    list_leads,
    get_lead_by_id,
    create_lead,
    update_lead,
)
from app.modules.crm.presentation.schemas import (
    LeadCreate,
    LeadUpdate,
    LeadRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[LeadRead], tags=["CRM - Leads"])
async def get_leads(
    empresa_id: Optional[UUID] = Query(None),
    campana_id: Optional[UUID] = Query(None),
    origen_lead: Optional[str] = Query(None),
    calificacion: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    asignado_vendedor_usuario_id: Optional[UUID] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista leads del tenant."""
    return await list_leads(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        campana_id=campana_id,
        origen_lead=origen_lead,
        calificacion=calificacion,
        estado=estado,
        asignado_vendedor_usuario_id=asignado_vendedor_usuario_id,
        buscar=buscar
    )


@router.get("/{lead_id}", response_model=LeadRead, tags=["CRM - Leads"])
async def get_lead(
    lead_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un lead por id."""
    try:
        return await get_lead_by_id(current_user.cliente_id, lead_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED, tags=["CRM - Leads"])
async def post_lead(
    data: LeadCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un lead."""
    return await create_lead(current_user.cliente_id, data)


@router.put("/{lead_id}", response_model=LeadRead, tags=["CRM - Leads"])
async def put_lead(
    lead_id: UUID,
    data: LeadUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un lead."""
    try:
        return await update_lead(current_user.cliente_id, lead_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
