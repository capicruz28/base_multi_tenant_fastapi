"""
Endpoints FastAPI para qms_inspeccion y qms_inspeccion_detalle.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.qms.application.services import (
    list_inspecciones,
    get_inspeccion_by_id,
    create_inspeccion,
    update_inspeccion,
    list_inspeccion_detalles,
    get_inspeccion_detalle_by_id,
    create_inspeccion_detalle,
    update_inspeccion_detalle,
)
from app.modules.qms.presentation.schemas import (
    InspeccionCreate,
    InspeccionUpdate,
    InspeccionRead,
    InspeccionDetalleCreate,
    InspeccionDetalleUpdate,
    InspeccionDetalleRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[InspeccionRead], tags=["QMS - Inspecciones"])
async def get_inspecciones(
    empresa_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    plan_inspeccion_id: Optional[UUID] = Query(None),
    resultado: Optional[str] = Query(None),
    lote: Optional[str] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista inspecciones del tenant."""
    return await list_inspecciones(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        plan_inspeccion_id=plan_inspeccion_id,
        resultado=resultado,
        lote=lote,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )


@router.get("/{inspeccion_id}", response_model=InspeccionRead, tags=["QMS - Inspecciones"])
async def get_inspeccion(
    inspeccion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una inspección por id."""
    try:
        return await get_inspeccion_by_id(current_user.cliente_id, inspeccion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=InspeccionRead, status_code=status.HTTP_201_CREATED, tags=["QMS - Inspecciones"])
async def post_inspeccion(
    data: InspeccionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una inspección."""
    return await create_inspeccion(current_user.cliente_id, data)


@router.put("/{inspeccion_id}", response_model=InspeccionRead, tags=["QMS - Inspecciones"])
async def put_inspeccion(
    inspeccion_id: UUID,
    data: InspeccionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una inspección."""
    try:
        return await update_inspeccion(current_user.cliente_id, inspeccion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Detalles de Inspección
@router.get("/{inspeccion_id}/detalles", response_model=List[InspeccionDetalleRead], tags=["QMS - Inspecciones"])
async def get_inspeccion_detalles(
    inspeccion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista detalles de una inspección."""
    return await list_inspeccion_detalles(current_user.cliente_id, inspeccion_id)


@router.post("/{inspeccion_id}/detalles", response_model=InspeccionDetalleRead, status_code=status.HTTP_201_CREATED, tags=["QMS - Inspecciones"])
async def post_inspeccion_detalle(
    inspeccion_id: UUID,
    data: InspeccionDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un detalle de inspección."""
    data.inspeccion_id = inspeccion_id
    return await create_inspeccion_detalle(current_user.cliente_id, data)


@router.get("/detalles/{inspeccion_detalle_id}", response_model=InspeccionDetalleRead, tags=["QMS - Inspecciones"])
async def get_inspeccion_detalle(
    inspeccion_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un detalle de inspección por id."""
    try:
        return await get_inspeccion_detalle_by_id(current_user.cliente_id, inspeccion_detalle_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/detalles/{inspeccion_detalle_id}", response_model=InspeccionDetalleRead, tags=["QMS - Inspecciones"])
async def put_inspeccion_detalle(
    inspeccion_detalle_id: UUID,
    data: InspeccionDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un detalle de inspección."""
    try:
        return await update_inspeccion_detalle(current_user.cliente_id, inspeccion_detalle_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
