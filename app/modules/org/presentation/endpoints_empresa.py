# app/modules/org/presentation/endpoints_empresa.py
"""Endpoints ORG - Empresa (tenant-scoped). client_id desde sesión efectiva (Etapa C1)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from typing import Optional

from app.core.authorization.rbac import require_permission
from app.core.exceptions import AuthorizationError, ConflictError, CustomException, NotFoundError
from app.modules.org.presentation.org_deps import (
    get_org_session_client_id,
    reject_legacy_cliente_query,
)
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.org.presentation.schemas import EmpresaCreate, EmpresaUpdate, EmpresaRead
from app.modules.org.application.services import empresa_service

router = APIRouter()


@router.get("", response_model=list[EmpresaRead], summary="Listar empresas")
async def listar_empresas(
    solo_activos: bool = True,
    buscar: Optional[str] = Query(None),
    _: None = Depends(reject_legacy_cliente_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.empresa.leer")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    """Lista empresas del tenant activo en sesión (todas las empresas del cliente)."""
    return await empresa_service.list_empresas_servicio(
        client_id=client_id,
        solo_activos=solo_activos,
        buscar=buscar,
    )


@router.get("/{empresa_id}", response_model=EmpresaRead, summary="Detalle empresa")
async def detalle_empresa(
    empresa_id: UUID,
    _: None = Depends(reject_legacy_cliente_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.empresa.leer")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    """Detalle de una empresa del tenant de sesión."""
    try:
        return await empresa_service.get_empresa_servicio(
            client_id=client_id,
            empresa_id=empresa_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.post("", response_model=EmpresaRead, status_code=status.HTTP_201_CREATED, summary="Crear empresa")
async def crear_empresa(
    data: EmpresaCreate,
    _: None = Depends(reject_legacy_cliente_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.empresa.crear")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    """Crea una empresa en el tenant de sesión. cliente_id no viene del body."""
    try:
        return await empresa_service.create_empresa_servicio(client_id=client_id, data=data)
    except (ConflictError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.put("/{empresa_id}", response_model=EmpresaRead, summary="Actualizar empresa")
async def actualizar_empresa(
    empresa_id: UUID,
    data: EmpresaUpdate,
    _: None = Depends(reject_legacy_cliente_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.empresa.actualizar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    """Actualiza una empresa del tenant de sesión."""
    try:
        return await empresa_service.update_empresa_servicio(
            client_id=client_id,
            empresa_id=empresa_id,
            data=data,
        )
    except (NotFoundError, ConflictError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.delete(
    "/{empresa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) empresa",
)
async def eliminar_empresa(
    empresa_id: UUID,
    _: None = Depends(reject_legacy_cliente_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.empresa.eliminar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    """Marca una empresa como inactiva dentro del tenant de sesión."""
    try:
        await empresa_service.delete_empresa_servicio(
            client_id=client_id,
            empresa_id=empresa_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.post(
    "/{empresa_id}/reactivar",
    response_model=EmpresaRead,
    summary="Reactivar empresa",
)
async def reactivar_empresa(
    empresa_id: UUID,
    _: None = Depends(reject_legacy_cliente_query),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.empresa.actualizar")),
    client_id: UUID = Depends(get_org_session_client_id),
):
    """Reactiva una empresa del tenant de sesión."""
    try:
        return await empresa_service.reactivar_empresa_servicio(
            client_id=client_id,
            empresa_id=empresa_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
