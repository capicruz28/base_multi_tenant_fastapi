"""Endpoints mfg_operacion."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mfg.application.services import list_operaciones, get_operacion_by_id, create_operacion, update_operacion
from app.modules.mfg.presentation.schemas import OperacionCreate, OperacionUpdate, OperacionRead
from app.core.exceptions import NotFoundError

router = APIRouter()

@router.get("", response_model=List[OperacionRead], tags=["MFG - Operaciones"])
async def get_operaciones(
    empresa_id: Optional[UUID] = Query(None),
    centro_trabajo_id: Optional[UUID] = Query(None),
    es_activo: Optional[bool] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_operaciones(current_user.cliente_id, empresa_id=empresa_id, centro_trabajo_id=centro_trabajo_id, es_activo=es_activo, buscar=buscar)

@router.get("/{operacion_id}", response_model=OperacionRead, tags=["MFG - Operaciones"])
async def get_operacion(operacion_id: UUID, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await get_operacion_by_id(current_user.cliente_id, operacion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("", response_model=OperacionRead, status_code=status.HTTP_201_CREATED, tags=["MFG - Operaciones"])
async def post_operacion(data: OperacionCreate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    return await create_operacion(current_user.cliente_id, data)

@router.put("/{operacion_id}", response_model=OperacionRead, tags=["MFG - Operaciones"])
async def put_operacion(operacion_id: UUID, data: OperacionUpdate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await update_operacion(current_user.cliente_id, operacion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
