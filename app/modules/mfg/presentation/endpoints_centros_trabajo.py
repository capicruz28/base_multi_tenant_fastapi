"""Endpoints mfg_centro_trabajo."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mfg.application.services import list_centros_trabajo, get_centro_trabajo_by_id, create_centro_trabajo, update_centro_trabajo
from app.modules.mfg.presentation.schemas import CentroTrabajoCreate, CentroTrabajoUpdate, CentroTrabajoRead
from app.core.exceptions import NotFoundError

router = APIRouter()

@router.get("", response_model=List[CentroTrabajoRead], tags=["MFG - Centros de Trabajo"])
async def get_centros_trabajo(
    empresa_id: Optional[UUID] = Query(None),
    estado_centro: Optional[str] = Query(None),
    es_activo: Optional[bool] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_centros_trabajo(current_user.cliente_id, empresa_id=empresa_id, estado_centro=estado_centro, es_activo=es_activo, buscar=buscar)

@router.get("/{centro_trabajo_id}", response_model=CentroTrabajoRead, tags=["MFG - Centros de Trabajo"])
async def get_centro_trabajo(centro_trabajo_id: UUID, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await get_centro_trabajo_by_id(current_user.cliente_id, centro_trabajo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("", response_model=CentroTrabajoRead, status_code=status.HTTP_201_CREATED, tags=["MFG - Centros de Trabajo"])
async def post_centro_trabajo(data: CentroTrabajoCreate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    return await create_centro_trabajo(current_user.cliente_id, data)

@router.put("/{centro_trabajo_id}", response_model=CentroTrabajoRead, tags=["MFG - Centros de Trabajo"])
async def put_centro_trabajo(centro_trabajo_id: UUID, data: CentroTrabajoUpdate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await update_centro_trabajo(current_user.cliente_id, centro_trabajo_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
