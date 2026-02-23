"""
Endpoints FastAPI para prc_promocion.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.prc.application.services import (
    list_promociones,
    get_promocion_by_id,
    create_promocion,
    update_promocion,
)
from app.modules.prc.presentation.schemas import (
    PromocionCreate,
    PromocionUpdate,
    PromocionRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PromocionRead], tags=["PRC - Promociones"])
async def get_promociones(
    empresa_id: Optional[UUID] = Query(None),
    tipo_promocion: Optional[str] = Query(None),
    aplica_a: Optional[str] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    categoria_id: Optional[UUID] = Query(None),
    solo_activos: bool = Query(True),
    solo_vigentes: bool = Query(False),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista promociones del tenant."""
    return await list_promociones(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_promocion=tipo_promocion,
        aplica_a=aplica_a,
        producto_id=producto_id,
        categoria_id=categoria_id,
        solo_activos=solo_activos,
        solo_vigentes=solo_vigentes,
        buscar=buscar
    )


@router.get("/{promocion_id}", response_model=PromocionRead, tags=["PRC - Promociones"])
async def get_promocion(
    promocion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una promoción por id."""
    try:
        return await get_promocion_by_id(current_user.cliente_id, promocion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PromocionRead, status_code=status.HTTP_201_CREATED, tags=["PRC - Promociones"])
async def post_promocion(
    data: PromocionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una promoción."""
    return await create_promocion(current_user.cliente_id, data)


@router.put("/{promocion_id}", response_model=PromocionRead, tags=["PRC - Promociones"])
async def put_promocion(
    promocion_id: UUID,
    data: PromocionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una promoción."""
    try:
        return await update_promocion(current_user.cliente_id, promocion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
