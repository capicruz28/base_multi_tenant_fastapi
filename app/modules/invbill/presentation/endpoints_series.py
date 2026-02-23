"""
Endpoints FastAPI para invbill_serie_comprobante.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.invbill.application.services import (
    list_series,
    get_serie_by_id,
    create_serie,
    update_serie,
)
from app.modules.invbill.presentation.schemas import (
    SerieComprobanteCreate,
    SerieComprobanteUpdate,
    SerieComprobanteRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[SerieComprobanteRead], tags=["INV_BILL - Series"])
async def get_series(
    empresa_id: Optional[UUID] = Query(None),
    tipo_comprobante: Optional[str] = Query(None),
    solo_activos: bool = Query(True),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista series de comprobantes del tenant."""
    return await list_series(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_comprobante=tipo_comprobante,
        solo_activos=solo_activos
    )


@router.get("/{serie_id}", response_model=SerieComprobanteRead, tags=["INV_BILL - Series"])
async def get_serie(
    serie_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una serie por id."""
    try:
        return await get_serie_by_id(current_user.cliente_id, serie_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=SerieComprobanteRead, status_code=status.HTTP_201_CREATED, tags=["INV_BILL - Series"])
async def post_serie(
    data: SerieComprobanteCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una serie."""
    return await create_serie(current_user.cliente_id, data)


@router.put("/{serie_id}", response_model=SerieComprobanteRead, tags=["INV_BILL - Series"])
async def put_serie(
    serie_id: UUID,
    data: SerieComprobanteUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una serie."""
    try:
        return await update_serie(current_user.cliente_id, serie_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
