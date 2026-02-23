# app/modules/org/presentation/endpoints_cargos.py
"""Endpoints ORG - Cargos. client_id desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.org.presentation.schemas import CargoCreate, CargoUpdate, CargoRead
from app.modules.org.application.services import cargo_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[CargoRead], summary="Listar cargos")
async def listar_cargos(
    empresa_id: Optional[UUID] = Query(None),
    solo_activos: bool = True,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.leer")),
):
    client_id = current_user.cliente_id
    return await cargo_service.list_cargos_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )


@router.get("/{cargo_id}", response_model=CargoRead, summary="Detalle cargo")
async def detalle_cargo(
    cargo_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.leer")),
):
    client_id = current_user.cliente_id
    try:
        return await cargo_service.get_cargo_servicio(
            client_id=client_id,
            cargo_id=cargo_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=CargoRead, status_code=201, summary="Crear cargo")
async def crear_cargo(
    data: CargoCreate,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.crear")),
):
    client_id = current_user.cliente_id
    return await cargo_service.create_cargo_servicio(client_id=client_id, data=data)


@router.put("/{cargo_id}", response_model=CargoRead, summary="Actualizar cargo")
async def actualizar_cargo(
    cargo_id: UUID,
    data: CargoUpdate,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.actualizar")),
):
    client_id = current_user.cliente_id
    try:
        return await cargo_service.update_cargo_servicio(
            client_id=client_id,
            cargo_id=cargo_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
