# app/modules/org/presentation/endpoints_parametros.py
"""Endpoints ORG - Parámetros del sistema. client_id desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.org.presentation.schemas import (
    ParametroCreate,
    ParametroUpdate,
    ParametroRead,
)
from app.modules.org.application.services import parametro_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[ParametroRead], summary="Listar parámetros")
async def listar_parametros(
    empresa_id: Optional[UUID] = Query(None),
    modulo_codigo: Optional[str] = Query(None),
    solo_activos: bool = True,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.leer")),
):
    client_id = current_user.cliente_id
    return await parametro_service.list_parametros_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        modulo_codigo=modulo_codigo,
        solo_activos=solo_activos,
    )


@router.get("/{parametro_id}", response_model=ParametroRead, summary="Detalle parámetro")
async def detalle_parametro(
    parametro_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.leer")),
):
    client_id = current_user.cliente_id
    try:
        return await parametro_service.get_parametro_servicio(
            client_id=client_id,
            parametro_id=parametro_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=ParametroRead, status_code=201, summary="Crear parámetro")
async def crear_parametro(
    data: ParametroCreate,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.crear")),
):
    client_id = current_user.cliente_id
    return await parametro_service.create_parametro_servicio(
        client_id=client_id,
        data=data,
    )


@router.put("/{parametro_id}", response_model=ParametroRead, summary="Actualizar parámetro")
async def actualizar_parametro(
    parametro_id: UUID,
    data: ParametroUpdate,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.area.actualizar")),
):
    client_id = current_user.cliente_id
    try:
        return await parametro_service.update_parametro_servicio(
            client_id=client_id,
            parametro_id=parametro_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
