# app/modules/inv/presentation/endpoints_stock.py
"""Endpoints INV - Stock. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.core.exceptions import NotFoundError, AuthorizationError, ValidationError
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import StockCreate, StockUpdate, StockRead
from app.modules.inv.application.services import stock_service

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "stock"


@router.get("", response_model=list[StockRead], summary="Listar stocks")
async def listar_stocks(
    producto_id: Optional[UUID] = Query(None, description="Filtrar por producto"),
    almacen_id: Optional[UUID] = Query(None, description="Filtrar por almacén"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista stocks de la empresa activa en sesión."""
    client_id = current_user.cliente_id
    try:
        return await stock_service.list_stocks_servicio(
            client_id=client_id,
            producto_id=producto_id,
            almacen_id=almacen_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/{stock_id}", response_model=StockRead, summary="Detalle stock")
async def detalle_stock(
    stock_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Detalle de un stock de la empresa activa."""
    client_id = current_user.cliente_id
    try:
        return await stock_service.get_stock_servicio(
            client_id=client_id,
            stock_id=stock_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get(
    "/producto/{producto_id}/almacen/{almacen_id}",
    response_model=Optional[StockRead],
    summary="Stock por producto y almacén",
)
async def stock_por_producto_almacen(
    producto_id: UUID,
    almacen_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Stock por producto y almacén en la empresa activa. Sin fila → null."""
    client_id = current_user.cliente_id
    try:
        return await stock_service.get_stock_by_producto_almacen_servicio(
            client_id=client_id,
            producto_id=producto_id,
            almacen_id=almacen_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "",
    response_model=StockRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear stock (Interno)",
    deprecated=True,
)
async def crear_stock(
    data: StockCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """(Interno) Crea un stock. empresa_id del body debe coincidir con la sesión."""
    client_id = current_user.cliente_id
    try:
        return await stock_service.create_stock_servicio(client_id=client_id, data=data)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put(
    "/{stock_id}",
    response_model=StockRead,
    summary="Actualizar stock (Interno)",
    deprecated=True,
)
async def actualizar_stock(
    stock_id: UUID,
    data: StockUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """(Interno) Actualiza un stock de la empresa activa."""
    client_id = current_user.cliente_id
    try:
        return await stock_service.update_stock_servicio(
            client_id=client_id,
            stock_id=stock_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
