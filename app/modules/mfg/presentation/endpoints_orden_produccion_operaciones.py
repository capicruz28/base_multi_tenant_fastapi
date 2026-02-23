"""Endpoints mfg_orden_produccion_operacion."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mfg.application.services import list_orden_produccion_operaciones, get_orden_produccion_operacion_by_id, create_orden_produccion_operacion, update_orden_produccion_operacion
from app.modules.mfg.presentation.schemas import OrdenProduccionOperacionCreate, OrdenProduccionOperacionUpdate, OrdenProduccionOperacionRead
from app.core.exceptions import NotFoundError

router = APIRouter()

@router.get("", response_model=List[OrdenProduccionOperacionRead], tags=["MFG - OP Operaciones"])
async def get_orden_produccion_operaciones(
    orden_produccion_id: Optional[UUID] = Query(None),
    centro_trabajo_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_orden_produccion_operaciones(current_user.cliente_id, orden_produccion_id=orden_produccion_id, centro_trabajo_id=centro_trabajo_id, estado=estado)

@router.get("/{op_operacion_id}", response_model=OrdenProduccionOperacionRead, tags=["MFG - OP Operaciones"])
async def get_orden_produccion_operacion(op_operacion_id: UUID, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await get_orden_produccion_operacion_by_id(current_user.cliente_id, op_operacion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("", response_model=OrdenProduccionOperacionRead, status_code=status.HTTP_201_CREATED, tags=["MFG - OP Operaciones"])
async def post_orden_produccion_operacion(data: OrdenProduccionOperacionCreate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    return await create_orden_produccion_operacion(current_user.cliente_id, data)

@router.put("/{op_operacion_id}", response_model=OrdenProduccionOperacionRead, tags=["MFG - OP Operaciones"])
async def put_orden_produccion_operacion(op_operacion_id: UUID, data: OrdenProduccionOperacionUpdate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await update_orden_produccion_operacion(current_user.cliente_id, op_operacion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
