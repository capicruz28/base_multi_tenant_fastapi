"""
Endpoints FastAPI para log_guia_remision y log_guia_remision_detalle.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.log.application.services import (
    list_guias_remision,
    get_guia_remision_by_id,
    create_guia_remision,
    update_guia_remision,
    list_guia_remision_detalles,
    get_guia_remision_detalle_by_id,
    create_guia_remision_detalle,
    update_guia_remision_detalle,
)
from app.modules.log.presentation.schemas import (
    GuiaRemisionCreate,
    GuiaRemisionUpdate,
    GuiaRemisionRead,
    GuiaRemisionDetalleCreate,
    GuiaRemisionDetalleUpdate,
    GuiaRemisionDetalleRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


# ============================================================================
# GUÍAS DE REMISIÓN
# ============================================================================

@router.get("", response_model=List[GuiaRemisionRead], tags=["LOG - Guías de Remisión"])
async def get_guias_remision(
    empresa_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    motivo_traslado: Optional[str] = Query(None),
    transportista_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista guías de remisión del tenant."""
    return await list_guias_remision(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        estado=estado,
        motivo_traslado=motivo_traslado,
        transportista_id=transportista_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )


@router.get("/{guia_remision_id}", response_model=GuiaRemisionRead, tags=["LOG - Guías de Remisión"])
async def get_guia_remision(
    guia_remision_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una guía de remisión por id."""
    try:
        return await get_guia_remision_by_id(current_user.cliente_id, guia_remision_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=GuiaRemisionRead, status_code=status.HTTP_201_CREATED, tags=["LOG - Guías de Remisión"])
async def post_guia_remision(
    data: GuiaRemisionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una guía de remisión."""
    return await create_guia_remision(current_user.cliente_id, data)


@router.put("/{guia_remision_id}", response_model=GuiaRemisionRead, tags=["LOG - Guías de Remisión"])
async def put_guia_remision(
    guia_remision_id: UUID,
    data: GuiaRemisionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una guía de remisión."""
    try:
        return await update_guia_remision(current_user.cliente_id, guia_remision_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# DETALLES DE GUÍA DE REMISIÓN
# ============================================================================

@router.get("/{guia_remision_id}/detalles", response_model=List[GuiaRemisionDetalleRead], tags=["LOG - Detalles de Guía"])
async def get_guia_remision_detalles(
    guia_remision_id: UUID,
    producto_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista detalles de una guía de remisión."""
    return await list_guia_remision_detalles(
        client_id=current_user.cliente_id,
        guia_remision_id=guia_remision_id,
        producto_id=producto_id
    )


@router.post("/{guia_remision_id}/detalles", response_model=GuiaRemisionDetalleRead, status_code=status.HTTP_201_CREATED, tags=["LOG - Detalles de Guía"])
async def post_guia_remision_detalle(
    guia_remision_id: UUID,
    data: GuiaRemisionDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un detalle de guía de remisión."""
    data.guia_remision_id = guia_remision_id
    return await create_guia_remision_detalle(current_user.cliente_id, data)


@router.get("/detalles/{guia_detalle_id}", response_model=GuiaRemisionDetalleRead, tags=["LOG - Detalles de Guía"])
async def get_guia_remision_detalle(
    guia_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un detalle por id."""
    try:
        return await get_guia_remision_detalle_by_id(current_user.cliente_id, guia_detalle_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/detalles/{guia_detalle_id}", response_model=GuiaRemisionDetalleRead, tags=["LOG - Detalles de Guía"])
async def put_guia_remision_detalle(
    guia_detalle_id: UUID,
    data: GuiaRemisionDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un detalle de guía de remisión."""
    try:
        return await update_guia_remision_detalle(current_user.cliente_id, guia_detalle_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
