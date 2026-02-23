"""
Endpoints FastAPI para wms_zona_almacen.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.wms.application.services import (
    list_zonas_almacen,
    get_zona_almacen_by_id,
    create_zona_almacen,
    update_zona_almacen,
)
from app.modules.wms.presentation.schemas import (
    ZonaAlmacenCreate,
    ZonaAlmacenUpdate,
    ZonaAlmacenRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ZonaAlmacenRead], tags=["WMS - Zonas de Almacén"])
async def get_zonas_almacen(
    almacen_id: Optional[UUID] = Query(None),
    tipo_zona: Optional[str] = Query(None),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista zonas de almacén del tenant."""
    return await list_zonas_almacen(
        client_id=current_user.cliente_id,
        almacen_id=almacen_id,
        tipo_zona=tipo_zona,
        solo_activos=solo_activos,
        buscar=buscar
    )


@router.get("/{zona_id}", response_model=ZonaAlmacenRead, tags=["WMS - Zonas de Almacén"])
async def get_zona_almacen(
    zona_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una zona de almacén por id."""
    try:
        return await get_zona_almacen_by_id(current_user.cliente_id, zona_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ZonaAlmacenRead, status_code=status.HTTP_201_CREATED, tags=["WMS - Zonas de Almacén"])
async def post_zona_almacen(
    data: ZonaAlmacenCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una zona de almacén."""
    return await create_zona_almacen(current_user.cliente_id, data)


@router.put("/{zona_id}", response_model=ZonaAlmacenRead, tags=["WMS - Zonas de Almacén"])
async def put_zona_almacen(
    zona_id: UUID,
    data: ZonaAlmacenUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una zona de almacén."""
    try:
        return await update_zona_almacen(current_user.cliente_id, zona_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
