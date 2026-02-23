# app/modules/org/presentation/endpoints_departamentos.py
"""Endpoints ORG - Departamentos. client_id desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.org.presentation.schemas import (
    DepartamentoCreate,
    DepartamentoUpdate,
    DepartamentoRead,
)
from app.modules.org.application.services import departamento_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[DepartamentoRead], summary="Listar departamentos")
async def listar_departamentos(
    empresa_id: Optional[UUID] = Query(None),
    solo_activos: bool = True,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.leer")),
):
    client_id = current_user.cliente_id
    return await departamento_service.list_departamentos_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )


@router.get("/{departamento_id}", response_model=DepartamentoRead, summary="Detalle departamento")
async def detalle_departamento(
    departamento_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.leer")),
):
    client_id = current_user.cliente_id
    try:
        return await departamento_service.get_departamento_servicio(
            client_id=client_id,
            departamento_id=departamento_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=DepartamentoRead, status_code=201, summary="Crear departamento")
async def crear_departamento(
    data: DepartamentoCreate,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.crear")),
):
    client_id = current_user.cliente_id
    return await departamento_service.create_departamento_servicio(
        client_id=client_id,
        data=data,
    )


@router.put("/{departamento_id}", response_model=DepartamentoRead, summary="Actualizar departamento")
async def actualizar_departamento(
    departamento_id: UUID,
    data: DepartamentoUpdate,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.actualizar")),
):
    client_id = current_user.cliente_id
    try:
        return await departamento_service.update_departamento_servicio(
            client_id=client_id,
            departamento_id=departamento_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
