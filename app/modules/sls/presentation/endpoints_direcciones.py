"""
Endpoints FastAPI para sls_cliente_direccion.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.sls.application.services import (
    list_direcciones,
    get_direccion_by_id,
    create_direccion,
    update_direccion,
)
from app.modules.sls.presentation.schemas import (
    ClienteDireccionCreate,
    ClienteDireccionUpdate,
    ClienteDireccionRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ClienteDireccionRead], tags=["SLS - Direcciones"])
async def get_direcciones(
    cliente_venta_id: Optional[UUID] = Query(None),
    solo_activos: bool = Query(True),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista direcciones del tenant."""
    return await list_direcciones(
        client_id=current_user.cliente_id,
        cliente_venta_id=cliente_venta_id,
        solo_activos=solo_activos
    )


@router.get("/{direccion_id}", response_model=ClienteDireccionRead, tags=["SLS - Direcciones"])
async def get_direccion(
    direccion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una direccion por id."""
    try:
        return await get_direccion_by_id(current_user.cliente_id, direccion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ClienteDireccionRead, status_code=status.HTTP_201_CREATED, tags=["SLS - Direcciones"])
async def post_direccion(
    data: ClienteDireccionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una direccion."""
    return await create_direccion(current_user.cliente_id, data)


@router.put("/{direccion_id}", response_model=ClienteDireccionRead, tags=["SLS - Direcciones"])
async def put_direccion(
    direccion_id: UUID,
    data: ClienteDireccionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una direccion."""
    try:
        return await update_direccion(current_user.cliente_id, direccion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
