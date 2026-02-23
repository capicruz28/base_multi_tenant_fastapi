"""
Endpoints FastAPI para invbill_comprobante_detalle.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.invbill.application.services import (
    list_comprobante_detalles,
    get_comprobante_detalle_by_id,
    create_comprobante_detalle,
    update_comprobante_detalle,
)
from app.modules.invbill.presentation.schemas import (
    ComprobanteDetalleCreate,
    ComprobanteDetalleUpdate,
    ComprobanteDetalleRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ComprobanteDetalleRead], tags=["INV_BILL - Detalles"])
async def get_comprobante_detalles(
    comprobante_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista detalles de comprobantes del tenant."""
    return await list_comprobante_detalles(
        client_id=current_user.cliente_id,
        comprobante_id=comprobante_id
    )


@router.get("/{comprobante_detalle_id}", response_model=ComprobanteDetalleRead, tags=["INV_BILL - Detalles"])
async def get_comprobante_detalle(
    comprobante_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un detalle por id."""
    try:
        return await get_comprobante_detalle_by_id(current_user.cliente_id, comprobante_detalle_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ComprobanteDetalleRead, status_code=status.HTTP_201_CREATED, tags=["INV_BILL - Detalles"])
async def post_comprobante_detalle(
    data: ComprobanteDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un detalle."""
    return await create_comprobante_detalle(current_user.cliente_id, data)


@router.put("/{comprobante_detalle_id}", response_model=ComprobanteDetalleRead, tags=["INV_BILL - Detalles"])
async def put_comprobante_detalle(
    comprobante_detalle_id: UUID,
    data: ComprobanteDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un detalle."""
    try:
        return await update_comprobante_detalle(current_user.cliente_id, comprobante_detalle_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
