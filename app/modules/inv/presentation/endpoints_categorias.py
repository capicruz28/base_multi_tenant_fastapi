# app/modules/inv/presentation/endpoints_categorias.py
"""Endpoints INV - Categorías. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import CategoriaCreate, CategoriaUpdate, CategoriaRead
from app.modules.inv.application.services import categoria_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[CategoriaRead], summary="Listar categorías")
async def listar_categorias(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    solo_activos: bool = Query(True, description="Solo categorías activas"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista categorías del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await categoria_service.list_categorias_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )


@router.get("/{categoria_id}", response_model=CategoriaRead, summary="Detalle categoría")
async def detalle_categoria(
    categoria_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Detalle de una categoría. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await categoria_service.get_categoria_servicio(
            client_id=client_id,
            categoria_id=categoria_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED, summary="Crear categoría")
async def crear_categoria(
    data: CategoriaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una categoría. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await categoria_service.create_categoria_servicio(client_id=client_id, data=data)


@router.put("/{categoria_id}", response_model=CategoriaRead, summary="Actualizar categoría")
async def actualizar_categoria(
    categoria_id: UUID,
    data: CategoriaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una categoría. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await categoria_service.update_categoria_servicio(
            client_id=client_id,
            categoria_id=categoria_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
