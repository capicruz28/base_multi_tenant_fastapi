"""
Endpoints FastAPI para qms_no_conformidad.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.qms.application.services import (
    list_no_conformidades,
    get_no_conformidad_by_id,
    create_no_conformidad,
    update_no_conformidad,
)
from app.modules.qms.presentation.schemas import (
    NoConformidadCreate,
    NoConformidadUpdate,
    NoConformidadRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[NoConformidadRead], tags=["QMS - No Conformidades"])
async def get_no_conformidades(
    empresa_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    origen: Optional[str] = Query(None),
    tipo_nc: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista no conformidades del tenant."""
    return await list_no_conformidades(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        origen=origen,
        tipo_nc=tipo_nc,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )


@router.get("/{no_conformidad_id}", response_model=NoConformidadRead, tags=["QMS - No Conformidades"])
async def get_no_conformidad(
    no_conformidad_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una no conformidad por id."""
    try:
        return await get_no_conformidad_by_id(current_user.cliente_id, no_conformidad_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=NoConformidadRead, status_code=status.HTTP_201_CREATED, tags=["QMS - No Conformidades"])
async def post_no_conformidad(
    data: NoConformidadCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una no conformidad."""
    return await create_no_conformidad(current_user.cliente_id, data)


@router.put("/{no_conformidad_id}", response_model=NoConformidadRead, tags=["QMS - No Conformidades"])
async def put_no_conformidad(
    no_conformidad_id: UUID,
    data: NoConformidadUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una no conformidad."""
    try:
        return await update_no_conformidad(current_user.cliente_id, no_conformidad_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
