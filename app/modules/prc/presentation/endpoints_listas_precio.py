"""
Endpoints FastAPI para prc_lista_precio y prc_lista_precio_detalle.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.prc.application.services import (
    list_listas_precio,
    get_lista_precio_by_id,
    create_lista_precio,
    update_lista_precio,
    list_lista_precio_detalles,
    get_lista_precio_detalle_by_id,
    create_lista_precio_detalle,
    update_lista_precio_detalle,
)
from app.modules.prc.presentation.schemas import (
    ListaPrecioCreate,
    ListaPrecioUpdate,
    ListaPrecioRead,
    ListaPrecioDetalleCreate,
    ListaPrecioDetalleUpdate,
    ListaPrecioDetalleRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


# ============================================================================
# LISTAS DE PRECIO
# ============================================================================

@router.get("", response_model=List[ListaPrecioRead], tags=["PRC - Listas de Precio"])
async def get_listas_precio(
    empresa_id: Optional[UUID] = Query(None),
    tipo_lista: Optional[str] = Query(None),
    solo_activos: bool = Query(True),
    solo_vigentes: bool = Query(False),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista listas de precio del tenant."""
    return await list_listas_precio(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_lista=tipo_lista,
        solo_activos=solo_activos,
        solo_vigentes=solo_vigentes,
        buscar=buscar
    )


@router.get("/{lista_precio_id}", response_model=ListaPrecioRead, tags=["PRC - Listas de Precio"])
async def get_lista_precio(
    lista_precio_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una lista de precio por id."""
    try:
        return await get_lista_precio_by_id(current_user.cliente_id, lista_precio_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ListaPrecioRead, status_code=status.HTTP_201_CREATED, tags=["PRC - Listas de Precio"])
async def post_lista_precio(
    data: ListaPrecioCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una lista de precio."""
    return await create_lista_precio(current_user.cliente_id, data)


@router.put("/{lista_precio_id}", response_model=ListaPrecioRead, tags=["PRC - Listas de Precio"])
async def put_lista_precio(
    lista_precio_id: UUID,
    data: ListaPrecioUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una lista de precio."""
    try:
        return await update_lista_precio(current_user.cliente_id, lista_precio_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# DETALLES DE LISTA DE PRECIO
# ============================================================================

@router.get("/{lista_precio_id}/detalles", response_model=List[ListaPrecioDetalleRead], tags=["PRC - Detalles de Lista"])
async def get_lista_precio_detalles(
    lista_precio_id: UUID,
    producto_id: Optional[UUID] = Query(None),
    solo_activos: bool = Query(True),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista detalles de una lista de precio."""
    return await list_lista_precio_detalles(
        client_id=current_user.cliente_id,
        lista_precio_id=lista_precio_id,
        producto_id=producto_id,
        solo_activos=solo_activos
    )


@router.post("/{lista_precio_id}/detalles", response_model=ListaPrecioDetalleRead, status_code=status.HTTP_201_CREATED, tags=["PRC - Detalles de Lista"])
async def post_lista_precio_detalle(
    lista_precio_id: UUID,
    data: ListaPrecioDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un detalle de lista de precio."""
    # Asegurar que el lista_precio_id del path coincida con el del body
    data.lista_precio_id = lista_precio_id
    return await create_lista_precio_detalle(current_user.cliente_id, data)


@router.get("/detalles/{lista_precio_detalle_id}", response_model=ListaPrecioDetalleRead, tags=["PRC - Detalles de Lista"])
async def get_lista_precio_detalle(
    lista_precio_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un detalle por id."""
    try:
        return await get_lista_precio_detalle_by_id(current_user.cliente_id, lista_precio_detalle_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/detalles/{lista_precio_detalle_id}", response_model=ListaPrecioDetalleRead, tags=["PRC - Detalles de Lista"])
async def put_lista_precio_detalle(
    lista_precio_detalle_id: UUID,
    data: ListaPrecioDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un detalle de lista de precio."""
    try:
        return await update_lista_precio_detalle(current_user.cliente_id, lista_precio_detalle_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
