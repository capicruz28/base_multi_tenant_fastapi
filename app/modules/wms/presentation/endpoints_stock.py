"""
Endpoints FastAPI para wms_stock_ubicacion.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.wms.application.services import (
    list_stock_ubicaciones,
    get_stock_ubicacion_by_id,
    create_stock_ubicacion,
    update_stock_ubicacion,
)
from app.modules.wms.presentation.schemas import (
    StockUbicacionCreate,
    StockUbicacionUpdate,
    StockUbicacionRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[StockUbicacionRead], tags=["WMS - Stock por Ubicación"])
async def get_stock_ubicaciones(
    almacen_id: Optional[UUID] = Query(None),
    ubicacion_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    estado_stock: Optional[str] = Query(None),
    lote: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista stock por ubicación del tenant."""
    return await list_stock_ubicaciones(
        client_id=current_user.cliente_id,
        almacen_id=almacen_id,
        ubicacion_id=ubicacion_id,
        producto_id=producto_id,
        estado_stock=estado_stock,
        lote=lote
    )


@router.get("/{stock_ubicacion_id}", response_model=StockUbicacionRead, tags=["WMS - Stock por Ubicación"])
async def get_stock_ubicacion(
    stock_ubicacion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un stock por ubicación por id."""
    try:
        return await get_stock_ubicacion_by_id(current_user.cliente_id, stock_ubicacion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=StockUbicacionRead, status_code=status.HTTP_201_CREATED, tags=["WMS - Stock por Ubicación"])
async def post_stock_ubicacion(
    data: StockUbicacionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un stock por ubicación."""
    return await create_stock_ubicacion(current_user.cliente_id, data)


@router.put("/{stock_ubicacion_id}", response_model=StockUbicacionRead, tags=["WMS - Stock por Ubicación"])
async def put_stock_ubicacion(
    stock_ubicacion_id: UUID,
    data: StockUbicacionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un stock por ubicación."""
    try:
        return await update_stock_ubicacion(current_user.cliente_id, stock_ubicacion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
