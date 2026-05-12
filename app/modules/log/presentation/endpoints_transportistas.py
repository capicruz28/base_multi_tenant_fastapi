"""
Endpoints FastAPI para log_transportista.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.log.application.services import (
    list_transportistas,
    get_transportista_by_id,
    create_transportista,
    update_transportista,
    delete_transportista,
    reactivar_transportista,
)
from app.modules.log.presentation.schemas import (
    TransportistaCreate,
    TransportistaUpdate,
    TransportistaRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()

MODULE_CODE = "log"
RESOURCE_CODE = "transportista"


@router.get("", response_model=List[TransportistaRead], tags=["LOG - Transportistas"])
async def get_transportistas(
    empresa_id: Optional[UUID] = Query(None),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista transportistas del tenant."""
    return await list_transportistas(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
        buscar=buscar
    )


@router.get("/{transportista_id}", response_model=TransportistaRead, tags=["LOG - Transportistas"])
async def get_transportista(
    transportista_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Obtiene un transportista por id."""
    try:
        return await get_transportista_by_id(
            current_user.cliente_id,
            transportista_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=TransportistaRead, status_code=status.HTTP_201_CREATED, tags=["LOG - Transportistas"])
async def post_transportista(
    data: TransportistaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea un transportista."""
    return await create_transportista(current_user.cliente_id, data)


@router.put("/{transportista_id}", response_model=TransportistaRead, tags=["LOG - Transportistas"])
async def put_transportista(
    transportista_id: UUID,
    data: TransportistaUpdate,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza un transportista."""
    try:
        return await update_transportista(
            current_user.cliente_id,
            transportista_id,
            data,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{transportista_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["LOG - Transportistas"],
)
async def delete_transportista_endpoint(
    transportista_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.eliminar")),
):
    """Baja lógica de transportista (es_activo = 0)."""
    try:
        await delete_transportista(
            current_user.cliente_id,
            transportista_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{transportista_id}/reactivar",
    response_model=TransportistaRead,
    tags=["LOG - Transportistas"],
)
async def reactivar_transportista_endpoint(
    transportista_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Reactiva transportista (es_activo = 1)."""
    try:
        return await reactivar_transportista(
            current_user.cliente_id,
            transportista_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
