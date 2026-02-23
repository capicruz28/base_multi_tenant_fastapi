"""
Endpoints FastAPI para sls_cotizacion.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.sls.application.services import (
    list_cotizaciones,
    get_cotizacion_by_id,
    create_cotizacion,
    update_cotizacion,
)
from app.modules.sls.presentation.schemas import (
    CotizacionCreate,
    CotizacionUpdate,
    CotizacionRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[CotizacionRead], tags=["SLS - Cotizaciones"])
async def get_cotizaciones(
    empresa_id: Optional[UUID] = Query(None),
    cliente_venta_id: Optional[UUID] = Query(None),
    vendedor_usuario_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista cotizaciones del tenant."""
    return await list_cotizaciones(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        cliente_venta_id=cliente_venta_id,
        vendedor_usuario_id=vendedor_usuario_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )


@router.get("/{cotizacion_id}", response_model=CotizacionRead, tags=["SLS - Cotizaciones"])
async def get_cotizacion(
    cotizacion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una cotizacion por id."""
    try:
        return await get_cotizacion_by_id(current_user.cliente_id, cotizacion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=CotizacionRead, status_code=status.HTTP_201_CREATED, tags=["SLS - Cotizaciones"])
async def post_cotizacion(
    data: CotizacionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una cotizacion."""
    return await create_cotizacion(current_user.cliente_id, data)


@router.put("/{cotizacion_id}", response_model=CotizacionRead, tags=["SLS - Cotizaciones"])
async def put_cotizacion(
    cotizacion_id: UUID,
    data: CotizacionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una cotizacion."""
    try:
        return await update_cotizacion(current_user.cliente_id, cotizacion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
