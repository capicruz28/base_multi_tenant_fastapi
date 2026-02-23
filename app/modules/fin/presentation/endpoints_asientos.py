"""
Endpoints FastAPI para fin_asiento_contable y fin_asiento_detalle.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.fin.application.services import (
    list_asientos_contables,
    get_asiento_contable_by_id,
    create_asiento_contable,
    update_asiento_contable,
    list_asiento_detalles,
    get_asiento_detalle_by_id,
    create_asiento_detalle,
    update_asiento_detalle,
)
from app.modules.fin.presentation.schemas import (
    AsientoContableCreate,
    AsientoContableUpdate,
    AsientoContableRead,
    AsientoDetalleCreate,
    AsientoDetalleUpdate,
    AsientoDetalleRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


# ============================================================================
# ASIENTOS CONTABLES
# ============================================================================

@router.get("", response_model=List[AsientoContableRead], tags=["FIN - Asientos Contables"])
async def get_asientos_contables(
    empresa_id: Optional[UUID] = Query(None),
    periodo_id: Optional[UUID] = Query(None),
    tipo_asiento: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    modulo_origen: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista asientos contables del tenant."""
    return await list_asientos_contables(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        periodo_id=periodo_id,
        tipo_asiento=tipo_asiento,
        estado=estado,
        modulo_origen=modulo_origen,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )


@router.get("/{asiento_id}", response_model=AsientoContableRead, tags=["FIN - Asientos Contables"])
async def get_asiento_contable(
    asiento_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un asiento contable por id."""
    try:
        return await get_asiento_contable_by_id(current_user.cliente_id, asiento_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=AsientoContableRead, status_code=status.HTTP_201_CREATED, tags=["FIN - Asientos Contables"])
async def post_asiento_contable(
    data: AsientoContableCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un asiento contable."""
    return await create_asiento_contable(current_user.cliente_id, data)


@router.put("/{asiento_id}", response_model=AsientoContableRead, tags=["FIN - Asientos Contables"])
async def put_asiento_contable(
    asiento_id: UUID,
    data: AsientoContableUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un asiento contable."""
    try:
        return await update_asiento_contable(current_user.cliente_id, asiento_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# DETALLES DE ASIENTO CONTABLE
# ============================================================================

@router.get("/{asiento_id}/detalles", response_model=List[AsientoDetalleRead], tags=["FIN - Detalles de Asiento"])
async def get_asiento_detalles(
    asiento_id: UUID,
    cuenta_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista detalles de un asiento contable."""
    return await list_asiento_detalles(
        client_id=current_user.cliente_id,
        asiento_id=asiento_id,
        cuenta_id=cuenta_id
    )


@router.post("/{asiento_id}/detalles", response_model=AsientoDetalleRead, status_code=status.HTTP_201_CREATED, tags=["FIN - Detalles de Asiento"])
async def post_asiento_detalle(
    asiento_id: UUID,
    data: AsientoDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un detalle de asiento contable."""
    data.asiento_id = asiento_id
    return await create_asiento_detalle(current_user.cliente_id, data)


@router.get("/detalles/{asiento_detalle_id}", response_model=AsientoDetalleRead, tags=["FIN - Detalles de Asiento"])
async def get_asiento_detalle(
    asiento_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un detalle por id."""
    try:
        return await get_asiento_detalle_by_id(current_user.cliente_id, asiento_detalle_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/detalles/{asiento_detalle_id}", response_model=AsientoDetalleRead, tags=["FIN - Detalles de Asiento"])
async def put_asiento_detalle(
    asiento_detalle_id: UUID,
    data: AsientoDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un detalle de asiento contable."""
    try:
        return await update_asiento_detalle(current_user.cliente_id, asiento_detalle_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
