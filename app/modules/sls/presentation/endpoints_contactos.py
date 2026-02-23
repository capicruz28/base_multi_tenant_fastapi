"""
Endpoints FastAPI para sls_cliente_contacto.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.sls.application.services import (
    list_contactos,
    get_contacto_by_id,
    create_contacto,
    update_contacto,
)
from app.modules.sls.presentation.schemas import (
    ClienteContactoCreate,
    ClienteContactoUpdate,
    ClienteContactoRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ClienteContactoRead], tags=["SLS - Contactos"])
async def get_contactos(
    cliente_venta_id: Optional[UUID] = Query(None),
    solo_activos: bool = Query(True),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista contactos del tenant."""
    return await list_contactos(
        client_id=current_user.cliente_id,
        cliente_venta_id=cliente_venta_id,
        solo_activos=solo_activos
    )


@router.get("/{contacto_id}", response_model=ClienteContactoRead, tags=["SLS - Contactos"])
async def get_contacto(
    contacto_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un contacto por id."""
    try:
        return await get_contacto_by_id(current_user.cliente_id, contacto_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ClienteContactoRead, status_code=status.HTTP_201_CREATED, tags=["SLS - Contactos"])
async def post_contacto(
    data: ClienteContactoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un contacto."""
    return await create_contacto(current_user.cliente_id, data)


@router.put("/{contacto_id}", response_model=ClienteContactoRead, tags=["SLS - Contactos"])
async def put_contacto(
    contacto_id: UUID,
    data: ClienteContactoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un contacto."""
    try:
        return await update_contacto(current_user.cliente_id, contacto_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
