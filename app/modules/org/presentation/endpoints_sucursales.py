# app/modules/org/presentation/endpoints_sucursales.py
"""Endpoints ORG - Sucursales. client_id desde current_user.cliente_id."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from uuid import UUID
from typing import Optional

from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.org.presentation.schemas import SucursalCreate, SucursalUpdate, SucursalRead
from app.modules.org.application.services import sucursal_service
from app.core.exceptions import NotFoundError

router = APIRouter()

_EMPRESA_ID_SCOPE_DESC = (
    "Si se informa, la fila debe pertenecer a esta empresa además del tenant (cliente)."
)


@router.get("", response_model=list[SucursalRead], summary="Listar sucursales")
async def listar_sucursales(
    empresa_id: Optional[UUID] = Query(None),
    solo_activos: bool = True,
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.sucursal.leer")),
):
    client_id = current_user.cliente_id
    return await sucursal_service.list_sucursales_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
        buscar=buscar,
    )


@router.post(
    "/{sucursal_id}/reactivar",
    response_model=SucursalRead,
    summary="Reactivar sucursal",
)
async def reactivar_sucursal(
    sucursal_id: UUID,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.sucursal.actualizar")),
):
    """Marca la sucursal como activa (es_activo = True) dentro del tenant."""
    client_id = current_user.cliente_id
    try:
        return await sucursal_service.reactivar_sucursal_servicio(
            client_id=client_id,
            sucursal_id=sucursal_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/{sucursal_id}", response_model=SucursalRead, summary="Detalle sucursal")
async def detalle_sucursal(
    sucursal_id: UUID,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.sucursal.leer")),
):
    client_id = current_user.cliente_id
    try:
        return await sucursal_service.get_sucursal_servicio(
            client_id=client_id,
            sucursal_id=sucursal_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=SucursalRead, status_code=201, summary="Crear sucursal")
async def crear_sucursal(
    data: SucursalCreate,
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.sucursal.crear")),
):
    client_id = current_user.cliente_id
    return await sucursal_service.create_sucursal_servicio(client_id=client_id, data=data)


@router.put("/{sucursal_id}", response_model=SucursalRead, summary="Actualizar sucursal")
async def actualizar_sucursal(
    sucursal_id: UUID,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    data: SucursalUpdate = Body(...),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.sucursal.actualizar")),
):
    client_id = current_user.cliente_id
    try:
        return await sucursal_service.update_sucursal_servicio(
            client_id=client_id,
            sucursal_id=sucursal_id,
            data=data,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.delete(
    "/{sucursal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar (baja lógica) sucursal",
)
async def eliminar_sucursal(
    sucursal_id: UUID,
    empresa_id: Optional[UUID] = Query(None, description=_EMPRESA_ID_SCOPE_DESC),
    current_user: UsuarioReadWithRoles = Depends(require_permission("org.sucursal.eliminar")),
):
    """Marca una sucursal como inactiva (baja lógica) dentro del tenant."""
    client_id = current_user.cliente_id
    try:
        await sucursal_service.delete_sucursal_servicio(
            client_id=client_id,
            sucursal_id=sucursal_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
