"""
Endpoints FastAPI para invbill_comprobante.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.invbill.application.services import (
    list_comprobantes,
    get_comprobante_by_id,
    create_comprobante,
    update_comprobante,
)
from app.modules.invbill.presentation.schemas import (
    ComprobanteCreate,
    ComprobanteUpdate,
    ComprobanteRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ComprobanteRead], tags=["INV_BILL - Comprobantes"])
async def get_comprobantes(
    empresa_id: Optional[UUID] = Query(None),
    tipo_comprobante: Optional[str] = Query(None),
    cliente_venta_id: Optional[UUID] = Query(None),
    pedido_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    estado_sunat: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista comprobantes del tenant."""
    return await list_comprobantes(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_comprobante=tipo_comprobante,
        cliente_venta_id=cliente_venta_id,
        pedido_id=pedido_id,
        estado=estado,
        estado_sunat=estado_sunat,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )


@router.get("/{comprobante_id}", response_model=ComprobanteRead, tags=["INV_BILL - Comprobantes"])
async def get_comprobante(
    comprobante_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un comprobante por id."""
    try:
        return await get_comprobante_by_id(current_user.cliente_id, comprobante_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ComprobanteRead, status_code=status.HTTP_201_CREATED, tags=["INV_BILL - Comprobantes"])
async def post_comprobante(
    data: ComprobanteCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un comprobante."""
    return await create_comprobante(current_user.cliente_id, data)


@router.put("/{comprobante_id}", response_model=ComprobanteRead, tags=["INV_BILL - Comprobantes"])
async def put_comprobante(
    comprobante_id: UUID,
    data: ComprobanteUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un comprobante."""
    try:
        return await update_comprobante(current_user.cliente_id, comprobante_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
