"""Endpoints mfg_ruta_fabricacion."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mfg.application.services import list_rutas_fabricacion, get_ruta_fabricacion_by_id, create_ruta_fabricacion, update_ruta_fabricacion
from app.modules.mfg.presentation.schemas import RutaFabricacionCreate, RutaFabricacionUpdate, RutaFabricacionRead
from app.core.exceptions import NotFoundError

router = APIRouter()

@router.get("", response_model=List[RutaFabricacionRead], tags=["MFG - Rutas de Fabricación"])
async def get_rutas_fabricacion(
    empresa_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    es_ruta_activa: Optional[bool] = Query(None),
    estado: Optional[str] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_rutas_fabricacion(current_user.cliente_id, empresa_id=empresa_id, producto_id=producto_id, es_ruta_activa=es_ruta_activa, estado=estado, buscar=buscar)

@router.get("/{ruta_id}", response_model=RutaFabricacionRead, tags=["MFG - Rutas de Fabricación"])
async def get_ruta_fabricacion(ruta_id: UUID, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await get_ruta_fabricacion_by_id(current_user.cliente_id, ruta_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("", response_model=RutaFabricacionRead, status_code=status.HTTP_201_CREATED, tags=["MFG - Rutas de Fabricación"])
async def post_ruta_fabricacion(data: RutaFabricacionCreate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    return await create_ruta_fabricacion(current_user.cliente_id, data)

@router.put("/{ruta_id}", response_model=RutaFabricacionRead, tags=["MFG - Rutas de Fabricación"])
async def put_ruta_fabricacion(ruta_id: UUID, data: RutaFabricacionUpdate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await update_ruta_fabricacion(current_user.cliente_id, ruta_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
