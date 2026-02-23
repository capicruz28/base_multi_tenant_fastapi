# app/modules/inv/presentation/endpoints_unidades_medida.py
"""Endpoints INV - Unidades de Medida. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import UnidadMedidaCreate, UnidadMedidaUpdate, UnidadMedidaRead
from app.modules.inv.application.services import unidad_medida_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[UnidadMedidaRead], summary="Listar unidades de medida")
async def listar_unidades_medida(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    solo_activos: bool = Query(True, description="Solo unidades activas"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista unidades de medida del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await unidad_medida_service.list_unidades_medida_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )


@router.get("/{unidad_medida_id}", response_model=UnidadMedidaRead, summary="Detalle unidad de medida")
async def detalle_unidad_medida(
    unidad_medida_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Detalle de una unidad de medida. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await unidad_medida_service.get_unidad_medida_servicio(
            client_id=client_id,
            unidad_medida_id=unidad_medida_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=UnidadMedidaRead, status_code=status.HTTP_201_CREATED, summary="Crear unidad de medida")
async def crear_unidad_medida(
    data: UnidadMedidaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una unidad de medida. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await unidad_medida_service.create_unidad_medida_servicio(client_id=client_id, data=data)


@router.put("/{unidad_medida_id}", response_model=UnidadMedidaRead, summary="Actualizar unidad de medida")
async def actualizar_unidad_medida(
    unidad_medida_id: UUID,
    data: UnidadMedidaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una unidad de medida. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await unidad_medida_service.update_unidad_medida_servicio(
            client_id=client_id,
            unidad_medida_id=unidad_medida_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
