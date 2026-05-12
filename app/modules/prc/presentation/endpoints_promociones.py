"""
Endpoints FastAPI para prc_promocion.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.prc.application.services import (
    list_promociones,
    get_promocion_by_id,
    create_promocion,
    update_promocion,
    desactivar_promocion,
    reactivar_promocion,
)
from app.modules.prc.presentation.schemas import (
    PromocionCreate,
    PromocionUpdate,
    PromocionRead,
)
from app.core.exceptions import NotFoundError

MODULE_CODE = "prc"
RESOURCE_CODE = "promocion"

router = APIRouter()

_EMPRESA_ID_SCOPE_DESC = (
    "Si se informa, la fila debe pertenecer a esta empresa además del tenant (cliente)."
)


@router.get("", response_model=List[PromocionRead], tags=["PRC - Promociones"])
async def get_promociones(
    empresa_id: Optional[UUID] = Query(None),
    tipo_promocion: Optional[str] = Query(None),
    aplica_a: Optional[str] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    categoria_id: Optional[UUID] = Query(None),
    solo_activos: bool = Query(True),
    solo_vigentes: bool = Query(False),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista promociones del tenant."""
    return await list_promociones(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_promocion=tipo_promocion,
        aplica_a=aplica_a,
        producto_id=producto_id,
        categoria_id=categoria_id,
        solo_activos=solo_activos,
        solo_vigentes=solo_vigentes,
        buscar=buscar,
    )


@router.post("", response_model=PromocionRead, status_code=status.HTTP_201_CREATED, tags=["PRC - Promociones"])
async def post_promocion(
    data: PromocionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una promoción."""
    return await create_promocion(current_user.cliente_id, data)


@router.post(
    "/{promocion_id}/reactivar",
    response_model=PromocionRead,
    summary="Reactivar promoción",
    tags=["PRC - Promociones"],
)
async def reactivar_promocion_endpoint(
    promocion_id: UUID,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Marca la promoción como activa (es_activo = True) dentro del tenant."""
    try:
        return await reactivar_promocion(
            current_user.cliente_id, promocion_id, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.delete(
    "/{promocion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar promoción (baja lógica)",
    tags=["PRC - Promociones"],
)
async def desactivar_promocion_endpoint(
    promocion_id: UUID,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.eliminar")),
):
    """Marca la promoción como inactiva (es_activo = False) dentro del tenant."""
    try:
        await desactivar_promocion(current_user.cliente_id, promocion_id, empresa_id=empresa_id)
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/{promocion_id}", response_model=PromocionRead, tags=["PRC - Promociones"])
async def get_promocion(
    promocion_id: UUID,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Obtiene una promoción por id."""
    try:
        return await get_promocion_by_id(
            current_user.cliente_id, promocion_id, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put("/{promocion_id}", response_model=PromocionRead, tags=["PRC - Promociones"])
async def put_promocion(
    promocion_id: UUID,
    data: PromocionUpdate,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una promoción."""
    try:
        return await update_promocion(
            current_user.cliente_id, promocion_id, data, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
