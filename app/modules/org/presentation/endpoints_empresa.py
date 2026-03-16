# app/modules/org/presentation/endpoints_empresa.py
"""Endpoints ORG - Empresa. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from typing import Optional

from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.org.presentation.schemas import EmpresaCreate, EmpresaUpdate, EmpresaRead
from app.modules.org.application.services import empresa_service
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=list[EmpresaRead], summary="Listar empresas")
async def listar_empresas(
    solo_activos: bool = True,
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.empresa.leer")),
):
    """Lista empresas del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await empresa_service.list_empresas_servicio(
        client_id=client_id,
        solo_activos=solo_activos,
        buscar=buscar,
    )


@router.get("/{empresa_id}", response_model=EmpresaRead, summary="Detalle empresa")
async def detalle_empresa(
    empresa_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.empresa.leer")),
):
    """Detalle de una empresa. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await empresa_service.get_empresa_servicio(
            client_id=client_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=EmpresaRead, status_code=status.HTTP_201_CREATED, summary="Crear empresa")
async def crear_empresa(
    data: EmpresaCreate,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.empresa.crear")),
):
    """Crea una empresa. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await empresa_service.create_empresa_servicio(client_id=client_id, data=data)


@router.put("/{empresa_id}", response_model=EmpresaRead, summary="Actualizar empresa")
async def actualizar_empresa(
    empresa_id: UUID,
    data: EmpresaUpdate,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.empresa.actualizar")),
):
    """Actualiza una empresa. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await empresa_service.update_empresa_servicio(
            client_id=client_id,
            empresa_id=empresa_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.delete(
    "/{empresa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) empresa",
)
async def eliminar_empresa(
    empresa_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.empresa.eliminar")),
):
    """Marca una empresa como inactiva (baja lógica) dentro del tenant."""
    client_id = current_user.cliente_id
    try:
        await empresa_service.delete_empresa_servicio(
            client_id=client_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{empresa_id}/reactivar",
    response_model=EmpresaRead,
    summary="Reactivar empresa",
)
async def reactivar_empresa(
    empresa_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.empresa.actualizar")),
):
    """Reactiva una empresa previamente dada de baja dentro del tenant."""
    client_id = current_user.cliente_id
    try:
        return await empresa_service.reactivar_empresa_servicio(
            client_id=client_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
