"""
Endpoints FastAPI para sls_pedido.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.sls.application.services import (
    list_pedidos,
    get_pedido_by_id,
    create_pedido,
    update_pedido,
)
from app.modules.sls.presentation.schemas import (
    PedidoCreate,
    PedidoUpdate,
    PedidoRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PedidoRead], tags=["SLS - Pedidos"])
async def get_pedidos(
    empresa_id: Optional[UUID] = Query(None),
    cliente_venta_id: Optional[UUID] = Query(None),
    vendedor_usuario_id: Optional[UUID] = Query(None),
    cotizacion_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista pedidos del tenant."""
    return await list_pedidos(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        cliente_venta_id=cliente_venta_id,
        vendedor_usuario_id=vendedor_usuario_id,
        cotizacion_id=cotizacion_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )


@router.get("/{pedido_id}", response_model=PedidoRead, tags=["SLS - Pedidos"])
async def get_pedido(
    pedido_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un pedido por id."""
    try:
        return await get_pedido_by_id(current_user.cliente_id, pedido_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PedidoRead, status_code=status.HTTP_201_CREATED, tags=["SLS - Pedidos"])
async def post_pedido(
    data: PedidoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un pedido."""
    return await create_pedido(current_user.cliente_id, data)


@router.put("/{pedido_id}", response_model=PedidoRead, tags=["SLS - Pedidos"])
async def put_pedido(
    pedido_id: UUID,
    data: PedidoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un pedido."""
    try:
        return await update_pedido(current_user.cliente_id, pedido_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
