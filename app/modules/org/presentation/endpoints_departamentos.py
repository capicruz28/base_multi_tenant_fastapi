# app/modules/org/presentation/endpoints_departamentos.py
"""Endpoints ORG - Departamentos. Company-scoped: empresa desde sesión JWT (Etapa B)."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from uuid import UUID
from typing import Optional

from app.core.authorization.rbac import require_permission
from app.core.exceptions import AuthorizationError, CustomException, NotFoundError
from app.modules.org.presentation.org_deps import (
    get_org_session_client_id,
    reject_legacy_empresa_query,
)
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.org.presentation.schemas import (
    DepartamentoCreate,
    DepartamentoUpdate,
    DepartamentoRead,
)
from app.modules.org.application.services import departamento_service

router = APIRouter()


@router.get("", response_model=list[DepartamentoRead], summary="Listar departamentos")
async def listar_departamentos(
    solo_activos: bool = True,
    buscar: Optional[str] = Query(None),
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.departamento.leer")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    return await departamento_service.list_departamentos_servicio(
        client_id=client_id,
        solo_activos=solo_activos,
        buscar=buscar,
    )


@router.post(
    "/{departamento_id}/reactivar",
    response_model=DepartamentoRead,
    summary="Reactivar departamento",
)
async def reactivar_departamento(
    departamento_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.departamento.actualizar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        return await departamento_service.reactivar_departamento_servicio(
            client_id=client_id,
            departamento_id=departamento_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.get("/{departamento_id}", response_model=DepartamentoRead, summary="Detalle departamento")
async def detalle_departamento(
    departamento_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.departamento.leer")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        return await departamento_service.get_departamento_servicio(
            client_id=client_id,
            departamento_id=departamento_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.post("", response_model=DepartamentoRead, status_code=201, summary="Crear departamento")
async def crear_departamento(
    data: DepartamentoCreate,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.departamento.crear")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        return await departamento_service.create_departamento_servicio(
            client_id=client_id, data=data
        )
    except (AuthorizationError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.put("/{departamento_id}", response_model=DepartamentoRead, summary="Actualizar departamento")
async def actualizar_departamento(
    departamento_id: UUID,
    data: DepartamentoUpdate = Body(...),
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.departamento.actualizar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        return await departamento_service.update_departamento_servicio(
            client_id=client_id,
            departamento_id=departamento_id,
            data=data,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.delete(
    "/{departamento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) departamento",
)
async def eliminar_departamento(
    departamento_id: UUID,
    _: None = Depends(reject_legacy_empresa_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.departamento.eliminar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    try:
        await departamento_service.delete_departamento_servicio(
            client_id=client_id,
            departamento_id=departamento_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
