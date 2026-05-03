"""Endpoints PUR - Recepciones Detalle. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pur.presentation.schemas import (
    RecepcionDetalleCreate,
    RecepcionDetalleUpdate,
    RecepcionDetalleRead,
)
from app.modules.pur.application.services import recepcion_detalle_service
from app.core.exceptions import NotFoundError

MODULE_CODE = "pur"
RESOURCE_CODE = "recepcion"

router = APIRouter()


@router.get(
    "",
    response_model=list[RecepcionDetalleRead],
    summary="Listar detalle de recepciones",
)
async def listar_recepciones_detalle(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    recepcion_id: Optional[UUID] = Query(
        None, description="Filtrar por cabecera de recepción"
    ),
    producto_id: Optional[UUID] = Query(
        None, description="Filtrar por producto en el detalle"
    ),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista líneas de recepciones del tenant. Filtro por cliente_id del token."""
    client_id = current_user.cliente_id
    return await recepcion_detalle_service.list_recepciones_detalle_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        recepcion_id=recepcion_id,
        producto_id=producto_id,
    )


@router.get(
    "/{recepcion_detalle_id}",
    response_model=RecepcionDetalleRead,
    summary="Detalle línea de recepción",
)
async def detalle_recepcion_detalle(
    recepcion_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Detalle de una línea de recepción. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await recepcion_detalle_service.get_recepcion_detalle_servicio(
            client_id=client_id,
            recepcion_detalle_id=recepcion_detalle_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "",
    response_model=RecepcionDetalleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear línea de recepción",
)
async def crear_recepcion_detalle(
    data: RecepcionDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una línea de recepción. cliente_id se asigna desde el contexto (tenant)."""
    client_id = current_user.cliente_id
    return await recepcion_detalle_service.create_recepcion_detalle_servicio(
        client_id=client_id,
        data=data,
    )


@router.put(
    "/{recepcion_detalle_id}",
    response_model=RecepcionDetalleRead,
    summary="Actualizar línea de recepción",
)
async def actualizar_recepcion_detalle(
    recepcion_detalle_id: UUID,
    data: RecepcionDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una línea de recepción. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await recepcion_detalle_service.update_recepcion_detalle_servicio(
            client_id=client_id,
            recepcion_detalle_id=recepcion_detalle_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
