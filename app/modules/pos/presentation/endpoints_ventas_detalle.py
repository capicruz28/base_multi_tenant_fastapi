"""
Endpoints FastAPI para pos_venta_detalle.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pos.application.services import (
    list_venta_detalles,
    get_venta_detalle_by_id,
    create_venta_detalle,
    update_venta_detalle,
)
from app.modules.pos.presentation.schemas import (
    VentaDetalleCreate,
    VentaDetalleUpdate,
    VentaDetalleRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[VentaDetalleRead], tags=["POS - Detalle de Ventas"])
async def get_venta_detalles(
    venta_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista detalles de venta POS. Opcionalmente filtra por venta_id."""
    return await list_venta_detalles(
        client_id=current_user.cliente_id,
        venta_id=venta_id,
    )


@router.get("/{venta_detalle_id}", response_model=VentaDetalleRead, tags=["POS - Detalle de Ventas"])
async def get_venta_detalle(
    venta_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un detalle de venta por id."""
    try:
        return await get_venta_detalle_by_id(current_user.cliente_id, venta_detalle_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=VentaDetalleRead, status_code=status.HTTP_201_CREATED, tags=["POS - Detalle de Ventas"])
async def post_venta_detalle(
    data: VentaDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un detalle de venta (línea de item)."""
    return await create_venta_detalle(current_user.cliente_id, data)


@router.put("/{venta_detalle_id}", response_model=VentaDetalleRead, tags=["POS - Detalle de Ventas"])
async def put_venta_detalle(
    venta_detalle_id: UUID,
    data: VentaDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un detalle de venta."""
    try:
        return await update_venta_detalle(current_user.cliente_id, venta_detalle_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
