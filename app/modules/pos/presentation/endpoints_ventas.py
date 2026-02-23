"""
Endpoints FastAPI para pos_venta.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pos.application.services import (
    list_ventas,
    get_venta_by_id,
    create_venta,
    update_venta,
)
from app.modules.pos.presentation.schemas import (
    VentaCreate,
    VentaUpdate,
    VentaRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[VentaRead], tags=["POS - Ventas"])
async def get_ventas(
    punto_venta_id: Optional[UUID] = Query(None),
    turno_caja_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista ventas POS del tenant."""
    return await list_ventas(
        client_id=current_user.cliente_id,
        punto_venta_id=punto_venta_id,
        turno_caja_id=turno_caja_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.get("/{venta_id}", response_model=VentaRead, tags=["POS - Ventas"])
async def get_venta(
    venta_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una venta POS por id."""
    try:
        return await get_venta_by_id(current_user.cliente_id, venta_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=VentaRead, status_code=status.HTTP_201_CREATED, tags=["POS - Ventas"])
async def post_venta(
    data: VentaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una venta POS."""
    return await create_venta(current_user.cliente_id, data)


@router.put("/{venta_id}", response_model=VentaRead, tags=["POS - Ventas"])
async def put_venta(
    venta_id: UUID,
    data: VentaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una venta POS (ej. anulación)."""
    try:
        return await update_venta(current_user.cliente_id, venta_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
