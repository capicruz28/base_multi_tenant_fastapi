"""Endpoints mfg_ruta_fabricacion_detalle."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mfg.application.services import list_ruta_fabricacion_detalles, get_ruta_fabricacion_detalle_by_id, create_ruta_fabricacion_detalle, update_ruta_fabricacion_detalle
from app.modules.mfg.presentation.schemas import RutaFabricacionDetalleCreate, RutaFabricacionDetalleUpdate, RutaFabricacionDetalleRead
from app.core.exceptions import NotFoundError

router = APIRouter()

@router.get("", response_model=List[RutaFabricacionDetalleRead], tags=["MFG - Ruta Fabricación Detalle"])
async def get_ruta_fabricacion_detalles(
    ruta_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_ruta_fabricacion_detalles(current_user.cliente_id, ruta_id=ruta_id)

@router.get("/{ruta_detalle_id}", response_model=RutaFabricacionDetalleRead, tags=["MFG - Ruta Fabricación Detalle"])
async def get_ruta_fabricacion_detalle(ruta_detalle_id: UUID, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await get_ruta_fabricacion_detalle_by_id(current_user.cliente_id, ruta_detalle_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("", response_model=RutaFabricacionDetalleRead, status_code=status.HTTP_201_CREATED, tags=["MFG - Ruta Fabricación Detalle"])
async def post_ruta_fabricacion_detalle(data: RutaFabricacionDetalleCreate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    return await create_ruta_fabricacion_detalle(current_user.cliente_id, data)

@router.put("/{ruta_detalle_id}", response_model=RutaFabricacionDetalleRead, tags=["MFG - Ruta Fabricación Detalle"])
async def put_ruta_fabricacion_detalle(ruta_detalle_id: UUID, data: RutaFabricacionDetalleUpdate, current_user: UsuarioReadWithRoles = Depends(get_current_active_user)):
    try:
        return await update_ruta_fabricacion_detalle(current_user.cliente_id, ruta_detalle_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
