"""Endpoints mfg_consumo_materiales."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mfg.application.services import list_consumo_materiales, get_consumo_materiales_by_id, create_consumo_materiales, update_consumo_materiales
from app.modules.mfg.presentation.schemas import ConsumoMaterialesCreate, ConsumoMaterialesUpdate, ConsumoMaterialesRead
from app.core.exceptions import NotFoundError

router = APIRouter()

@router.get("", response_model=List[ConsumoMaterialesRead], tags=["MFG - Consumo Materiales"])
async def get_consumo_materiales(
    orden_produccion_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_consumo_materiales(current_user.cliente_id, orden_produccion_id=orden_produccion_id, producto_id=producto_id)

@router.get("/{consumo_id}", response_model=ConsumoMaterialesRead, tags=["MFG - Consumo Materiales"])
async def get_consumo_materiales_by_id_endpoint(consumo_id: UUID, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await get_consumo_materiales_by_id(current_user.cliente_id, consumo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("", response_model=ConsumoMaterialesRead, status_code=status.HTTP_201_CREATED, tags=["MFG - Consumo Materiales"])
async def post_consumo_materiales(data: ConsumoMaterialesCreate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    return await create_consumo_materiales(current_user.cliente_id, data)

@router.put("/{consumo_id}", response_model=ConsumoMaterialesRead, tags=["MFG - Consumo Materiales"])
async def put_consumo_materiales(consumo_id: UUID, data: ConsumoMaterialesUpdate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await update_consumo_materiales(current_user.cliente_id, consumo_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
