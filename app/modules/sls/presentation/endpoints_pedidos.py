"""
Endpoints FastAPI para sls_pedido.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi import status

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.sls.application.services import (
    list_pedidos,
    get_pedido_by_id,
    create_pedido,
    update_pedido,
    get_detalle_pedido,
    put_detalle_pedido,
    confirmar_pedido,
    aprobar_pedido,
    anular_pedido,
)
from app.modules.sls.presentation.schemas import (
    PedidoCreate,
    PedidoUpdate,
    PedidoRead,
    PedidoDetalleCreate,
    PedidoDetalleRead,
    PedidoAnularBody,
)
from app.core.exceptions import NotFoundError

MODULE_CODE = "sls"
RESOURCE_CODE = "pedido"

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
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
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
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
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
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea un pedido."""
    return await create_pedido(current_user.cliente_id, data)


@router.put("/{pedido_id}", response_model=PedidoRead, tags=["SLS - Pedidos"])
async def put_pedido(
    pedido_id: UUID,
    data: PedidoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza un pedido."""
    try:
        return await update_pedido(current_user.cliente_id, pedido_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{pedido_id}/detalle", response_model=List[PedidoDetalleRead], tags=["SLS - Pedidos"])
async def get_pedido_detalle(
    pedido_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Obtiene el detalle (embebido) de un pedido."""
    return await get_detalle_pedido(current_user.cliente_id, pedido_id)


@router.put("/{pedido_id}/detalle", response_model=List[PedidoDetalleRead], tags=["SLS - Pedidos"])
async def put_pedido_detalle(
    pedido_id: UUID,
    items: List[PedidoDetalleCreate] = Body(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Reemplaza el detalle (embebido) de un pedido. Solo en borrador."""
    return await put_detalle_pedido(current_user.cliente_id, pedido_id, items)


@router.post("/{pedido_id}/confirmar", response_model=PedidoRead, tags=["SLS - Pedidos"])
async def post_confirmar_pedido(
    pedido_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    return await confirmar_pedido(current_user.cliente_id, pedido_id)


@router.post("/{pedido_id}/aprobar", response_model=PedidoRead, tags=["SLS - Pedidos"])
async def post_aprobar_pedido(
    pedido_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    return await aprobar_pedido(
        current_user.cliente_id,
        pedido_id,
        aprobado_por_usuario_id=current_user.usuario_id,
    )


@router.post("/{pedido_id}/anular", response_model=PedidoRead, tags=["SLS - Pedidos"])
async def post_anular_pedido(
    pedido_id: UUID,
    body: PedidoAnularBody = Body(default_factory=PedidoAnularBody),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    return await anular_pedido(current_user.cliente_id, pedido_id, motivo=body.motivo_anulacion)
