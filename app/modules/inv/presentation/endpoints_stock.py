# app/modules/inv/presentation/endpoints_stock.py
"""Endpoints INV - Stock. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import StockCreate, StockUpdate, StockRead
from app.modules.inv.application.services import stock_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[StockRead], summary="Listar stocks")
async def listar_stocks(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    producto_id: Optional[UUID] = Query(None, description="Filtrar por producto"),
    almacen_id: Optional[UUID] = Query(None, description="Filtrar por almacén"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista stocks del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await stock_service.list_stocks_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        almacen_id=almacen_id,
    )


@router.get("/{stock_id}", response_model=StockRead, summary="Detalle stock")
async def detalle_stock(
    stock_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Detalle de un stock. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await stock_service.get_stock_servicio(
            client_id=client_id,
            stock_id=stock_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/producto/{producto_id}/almacen/{almacen_id}", response_model=Optional[StockRead], summary="Stock por producto y almacén")
async def stock_por_producto_almacen(
    producto_id: UUID,
    almacen_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene stock por producto y almacén. Útil para consultas rápidas."""
    client_id = current_user.cliente_id
    return await stock_service.get_stock_by_producto_almacen_servicio(
        client_id=client_id,
        producto_id=producto_id,
        almacen_id=almacen_id,
    )


@router.post("", response_model=StockRead, status_code=status.HTTP_201_CREATED, summary="Crear stock")
async def crear_stock(
    data: StockCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un stock. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await stock_service.create_stock_servicio(client_id=client_id, data=data)


@router.put("/{stock_id}", response_model=StockRead, summary="Actualizar stock")
async def actualizar_stock(
    stock_id: UUID,
    data: StockUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un stock. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await stock_service.update_stock_servicio(
            client_id=client_id,
            stock_id=stock_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
