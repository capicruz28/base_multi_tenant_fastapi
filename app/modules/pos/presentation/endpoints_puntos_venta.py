"""
Endpoints FastAPI para pos_punto_venta.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pos.application.services import (
    list_puntos_venta,
    get_punto_venta_by_id,
    create_punto_venta,
    update_punto_venta,
)
from app.modules.pos.presentation.schemas import (
    PuntoVentaCreate,
    PuntoVentaUpdate,
    PuntoVentaRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PuntoVentaRead], tags=["POS - Puntos de Venta"])
async def get_puntos_venta(
    empresa_id: Optional[UUID] = Query(None),
    sucursal_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    es_activo: Optional[bool] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista puntos de venta del tenant."""
    return await list_puntos_venta(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        sucursal_id=sucursal_id,
        estado=estado,
        es_activo=es_activo,
        buscar=buscar,
    )


@router.get("/{punto_venta_id}", response_model=PuntoVentaRead, tags=["POS - Puntos de Venta"])
async def get_punto_venta(
    punto_venta_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un punto de venta por id."""
    try:
        return await get_punto_venta_by_id(current_user.cliente_id, punto_venta_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PuntoVentaRead, status_code=status.HTTP_201_CREATED, tags=["POS - Puntos de Venta"])
async def post_punto_venta(
    data: PuntoVentaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un punto de venta."""
    return await create_punto_venta(current_user.cliente_id, data)


@router.put("/{punto_venta_id}", response_model=PuntoVentaRead, tags=["POS - Puntos de Venta"])
async def put_punto_venta(
    punto_venta_id: UUID,
    data: PuntoVentaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un punto de venta."""
    try:
        return await update_punto_venta(current_user.cliente_id, punto_venta_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
