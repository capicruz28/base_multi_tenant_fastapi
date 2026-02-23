"""Endpoints mfg_orden_produccion."""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mfg.application.services import (
    list_ordenes_produccion,
    get_orden_produccion_by_id,
    create_orden_produccion,
    update_orden_produccion,
)
from app.modules.mfg.presentation.schemas import (
    OrdenProduccionCreate,
    OrdenProduccionUpdate,
    OrdenProduccionRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[OrdenProduccionRead], tags=["MFG - Ordenes de Produccion"])
async def get_ordenes_produccion(
    empresa_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("mfg.orden_produccion.leer")),
):
    return await list_ordenes_produccion(
        current_user.cliente_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.get("/{orden_produccion_id}", response_model=OrdenProduccionRead, tags=["MFG - Ordenes de Produccion"])
async def get_orden_produccion(
    orden_produccion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("mfg.orden_produccion.leer")),
):
    try:
        return await get_orden_produccion_by_id(current_user.cliente_id, orden_produccion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=OrdenProduccionRead, status_code=status.HTTP_201_CREATED, tags=["MFG - Ordenes de Produccion"])
async def post_orden_produccion(
    data: OrdenProduccionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("mfg.orden_produccion.crear")),
):
    return await create_orden_produccion(current_user.cliente_id, data)


@router.put("/{orden_produccion_id}", response_model=OrdenProduccionRead, tags=["MFG - Ordenes de Produccion"])
async def put_orden_produccion(
    orden_produccion_id: UUID,
    data: OrdenProduccionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("mfg.orden_produccion.actualizar")),
):
    try:
        return await update_orden_produccion(current_user.cliente_id, orden_produccion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
