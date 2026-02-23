"""Endpoints mfg_lista_materiales (BOM)."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mfg.application.services import list_listas_materiales, get_lista_materiales_by_id, create_lista_materiales, update_lista_materiales
from app.modules.mfg.presentation.schemas import ListaMaterialesCreate, ListaMaterialesUpdate, ListaMaterialesRead
from app.core.exceptions import NotFoundError

router = APIRouter()

@router.get("", response_model=List[ListaMaterialesRead], tags=["MFG - Listas de Materiales (BOM)"])
async def get_listas_materiales(
    empresa_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    es_bom_activa: Optional[bool] = Query(None),
    estado: Optional[str] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_listas_materiales(current_user.cliente_id, empresa_id=empresa_id, producto_id=producto_id, es_bom_activa=es_bom_activa, estado=estado, buscar=buscar)

@router.get("/{bom_id}", response_model=ListaMaterialesRead, tags=["MFG - Listas de Materiales (BOM)"])
async def get_lista_materiales(bom_id: UUID, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await get_lista_materiales_by_id(current_user.cliente_id, bom_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("", response_model=ListaMaterialesRead, status_code=status.HTTP_201_CREATED, tags=["MFG - Listas de Materiales (BOM)"])
async def post_lista_materiales(data: ListaMaterialesCreate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    return await create_lista_materiales(current_user.cliente_id, data)

@router.put("/{bom_id}", response_model=ListaMaterialesRead, tags=["MFG - Listas de Materiales (BOM)"])
async def put_lista_materiales(bom_id: UUID, data: ListaMaterialesUpdate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await update_lista_materiales(current_user.cliente_id, bom_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
