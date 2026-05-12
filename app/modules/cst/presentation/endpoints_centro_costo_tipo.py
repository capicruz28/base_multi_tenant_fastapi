"""Endpoints cst tipos de centro de costo."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.cst.application.services import (
    list_centro_costo_tipo,
    get_centro_costo_tipo_by_id,
    create_centro_costo_tipo,
    update_centro_costo_tipo,
    deactivate_centro_costo_tipo,
    reactivate_centro_costo_tipo,
)
from app.modules.cst.presentation.schemas import (
    CentroCostoTipoCreate,
    CentroCostoTipoUpdate,
    CentroCostoTipoRead,
)
from app.core.exceptions import NotFoundError

MODULE_CODE = "cst"
RESOURCE_CODE = "centro_costo_tipo"

router = APIRouter()


@router.get("", response_model=List[CentroCostoTipoRead])
async def get_tipos_centro_costo(
    empresa_id: Optional[UUID] = Query(None),
    tipo_clasificacion: Optional[str] = Query(None),
    es_activo: Optional[bool] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    return await list_centro_costo_tipo(
        current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_clasificacion=tipo_clasificacion,
        es_activo=es_activo,
        buscar=buscar,
    )


@router.get("/{cc_tipo_id}", response_model=CentroCostoTipoRead)
async def get_tipo_centro_costo(
    cc_tipo_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    try:
        return await get_centro_costo_tipo_by_id(
            current_user.cliente_id, cc_tipo_id, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=CentroCostoTipoRead, status_code=status.HTTP_201_CREATED)
async def post_tipo_centro_costo(
    data: CentroCostoTipoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    return await create_centro_costo_tipo(current_user.cliente_id, data)


@router.put("/{cc_tipo_id}", response_model=CentroCostoTipoRead)
async def put_tipo_centro_costo(
    cc_tipo_id: UUID,
    data: CentroCostoTipoUpdate,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    try:
        return await update_centro_costo_tipo(
            current_user.cliente_id, cc_tipo_id, data, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{cc_tipo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar tipo de centro de costo (baja lógica)",
)
async def delete_tipo_centro_costo(
    cc_tipo_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.eliminar")),
):
    try:
        await deactivate_centro_costo_tipo(
            current_user.cliente_id, cc_tipo_id, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{cc_tipo_id}/reactivar",
    response_model=CentroCostoTipoRead,
    summary="Reactivar tipo de centro de costo",
)
async def post_reactivar_tipo_centro_costo(
    cc_tipo_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    try:
        return await reactivate_centro_costo_tipo(
            current_user.cliente_id, cc_tipo_id, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
