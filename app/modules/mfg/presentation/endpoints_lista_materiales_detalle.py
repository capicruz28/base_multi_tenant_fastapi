"""Endpoints mfg_lista_materiales_detalle."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mfg.application.services import list_lista_materiales_detalles, get_lista_materiales_detalle_by_id, create_lista_materiales_detalle, update_lista_materiales_detalle
from app.modules.mfg.presentation.schemas import ListaMaterialesDetalleCreate, ListaMaterialesDetalleUpdate, ListaMaterialesDetalleRead
from app.core.exceptions import NotFoundError

router = APIRouter()

@router.get("", response_model=List[ListaMaterialesDetalleRead], tags=["MFG - BOM Detalle"])
async def get_lista_materiales_detalles(
    bom_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_lista_materiales_detalles(current_user.cliente_id, bom_id=bom_id)

@router.get("/{bom_detalle_id}", response_model=ListaMaterialesDetalleRead, tags=["MFG - BOM Detalle"])
async def get_lista_materiales_detalle(bom_detalle_id: UUID, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await get_lista_materiales_detalle_by_id(current_user.cliente_id, bom_detalle_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("", response_model=ListaMaterialesDetalleRead, status_code=status.HTTP_201_CREATED, tags=["MFG - BOM Detalle"])
async def post_lista_materiales_detalle(data: ListaMaterialesDetalleCreate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    return await create_lista_materiales_detalle(current_user.cliente_id, data)

@router.put("/{bom_detalle_id}", response_model=ListaMaterialesDetalleRead, tags=["MFG - BOM Detalle"])
async def put_lista_materiales_detalle(bom_detalle_id: UUID, data: ListaMaterialesDetalleUpdate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await update_lista_materiales_detalle(current_user.cliente_id, bom_detalle_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
