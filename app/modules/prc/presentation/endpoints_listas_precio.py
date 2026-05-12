"""
Endpoints FastAPI para prc_lista_precio y prc_lista_precio_detalle.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.core.exceptions import NotFoundError
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.prc.application.services import (
    list_listas_precio,
    get_lista_precio_by_id,
    create_lista_precio,
    update_lista_precio,
    desactivar_lista_precio,
    reactivar_lista_precio,
    list_lista_precio_detalles,
    get_lista_precio_detalle_by_id,
    create_lista_precio_detalle,
    update_lista_precio_detalle,
)
from app.modules.prc.presentation.schemas import (
    ListaPrecioCreate,
    ListaPrecioUpdate,
    ListaPrecioRead,
    ListaPrecioDetalleCreate,
    ListaPrecioDetalleUpdate,
    ListaPrecioDetalleRead,
)

MODULE_CODE = "prc"
RESOURCE_CODE = "lista_precio"

router = APIRouter()

_EMPRESA_ID_SCOPE_DESC = (
    "Si se informa, la fila debe pertenecer a esta empresa además del tenant (cliente)."
)


# ============================================================================
# LISTAS DE PRECIO
# ============================================================================

@router.get("", response_model=List[ListaPrecioRead], tags=["PRC - Listas de Precio"])
async def get_listas_precio(
    empresa_id: Optional[UUID] = Query(None),
    tipo_lista: Optional[str] = Query(None),
    solo_activos: bool = Query(True),
    solo_vigentes: bool = Query(False),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista listas de precio del tenant."""
    return await list_listas_precio(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_lista=tipo_lista,
        solo_activos=solo_activos,
        solo_vigentes=solo_vigentes,
        buscar=buscar,
    )


@router.post("", response_model=ListaPrecioRead, status_code=status.HTTP_201_CREATED, tags=["PRC - Listas de Precio"])
async def post_lista_precio(
    data: ListaPrecioCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una lista de precio."""
    return await create_lista_precio(current_user.cliente_id, data)


@router.post(
    "/{lista_precio_id}/reactivar",
    response_model=ListaPrecioRead,
    summary="Reactivar lista de precio",
    tags=["PRC - Listas de Precio"],
)
async def reactivar_lista_precio_endpoint(
    lista_precio_id: UUID,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Marca la lista como activa (es_activo = True) dentro del tenant."""
    try:
        return await reactivar_lista_precio(
            current_user.cliente_id, lista_precio_id, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.delete(
    "/{lista_precio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar lista de precio (baja lógica)",
    tags=["PRC - Listas de Precio"],
)
async def desactivar_lista_precio_endpoint(
    lista_precio_id: UUID,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.eliminar")),
):
    """Marca la lista como inactiva (es_activo = False) dentro del tenant."""
    try:
        await desactivar_lista_precio(
            current_user.cliente_id, lista_precio_id, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/{lista_precio_id}", response_model=ListaPrecioRead, tags=["PRC - Listas de Precio"])
async def get_lista_precio(
    lista_precio_id: UUID,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Obtiene una lista de precio por id."""
    try:
        return await get_lista_precio_by_id(
            current_user.cliente_id, lista_precio_id, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put("/{lista_precio_id}", response_model=ListaPrecioRead, tags=["PRC - Listas de Precio"])
async def put_lista_precio(
    lista_precio_id: UUID,
    data: ListaPrecioUpdate,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una lista de precio."""
    try:
        return await update_lista_precio(
            current_user.cliente_id, lista_precio_id, data, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# ============================================================================
# DETALLES DE LISTA DE PRECIO
# ============================================================================

@router.get(
    "/{lista_precio_id}/detalles",
    response_model=List[ListaPrecioDetalleRead],
    tags=["PRC - Detalles de Lista"],
)
async def get_lista_precio_detalles(
    lista_precio_id: UUID,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    producto_id: Optional[UUID] = Query(None),
    solo_activos: bool = Query(True),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista detalles de una lista de precio."""
    return await list_lista_precio_detalles(
        client_id=current_user.cliente_id,
        lista_precio_id=lista_precio_id,
        producto_id=producto_id,
        solo_activos=solo_activos,
        empresa_id=empresa_id,
    )


@router.post(
    "/{lista_precio_id}/detalles",
    response_model=ListaPrecioDetalleRead,
    status_code=status.HTTP_201_CREATED,
    tags=["PRC - Detalles de Lista"],
)
async def post_lista_precio_detalle(
    lista_precio_id: UUID,
    data: ListaPrecioDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea un detalle de lista de precio."""
    data.lista_precio_id = lista_precio_id
    try:
        return await create_lista_precio_detalle(current_user.cliente_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get(
    "/detalles/{lista_precio_detalle_id}",
    response_model=ListaPrecioDetalleRead,
    tags=["PRC - Detalles de Lista"],
)
async def get_lista_precio_detalle(
    lista_precio_detalle_id: UUID,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Obtiene un detalle por id."""
    try:
        return await get_lista_precio_detalle_by_id(
            current_user.cliente_id, lista_precio_detalle_id, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put(
    "/detalles/{lista_precio_detalle_id}",
    response_model=ListaPrecioDetalleRead,
    tags=["PRC - Detalles de Lista"],
)
async def put_lista_precio_detalle(
    lista_precio_detalle_id: UUID,
    data: ListaPrecioDetalleUpdate,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza un detalle de lista de precio."""
    try:
        return await update_lista_precio_detalle(
            current_user.cliente_id, lista_precio_detalle_id, data, empresa_id=empresa_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
