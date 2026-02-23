"""
Endpoints FastAPI para log_transportista.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.log.application.services import (
    list_transportistas,
    get_transportista_by_id,
    create_transportista,
    update_transportista,
)
from app.modules.log.presentation.schemas import (
    TransportistaCreate,
    TransportistaUpdate,
    TransportistaRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[TransportistaRead], tags=["LOG - Transportistas"])
async def get_transportistas(
    empresa_id: Optional[UUID] = Query(None),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista transportistas del tenant."""
    return await list_transportistas(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
        buscar=buscar
    )


@router.get("/{transportista_id}", response_model=TransportistaRead, tags=["LOG - Transportistas"])
async def get_transportista(
    transportista_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un transportista por id."""
    try:
        return await get_transportista_by_id(current_user.cliente_id, transportista_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=TransportistaRead, status_code=status.HTTP_201_CREATED, tags=["LOG - Transportistas"])
async def post_transportista(
    data: TransportistaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un transportista."""
    return await create_transportista(current_user.cliente_id, data)


@router.put("/{transportista_id}", response_model=TransportistaRead, tags=["LOG - Transportistas"])
async def put_transportista(
    transportista_id: UUID,
    data: TransportistaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un transportista."""
    try:
        return await update_transportista(current_user.cliente_id, transportista_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
