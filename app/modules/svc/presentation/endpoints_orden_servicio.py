"""Endpoints svc orden de servicio."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.svc.application.services import (
    list_orden_servicio,
    get_orden_servicio_by_id,
    create_orden_servicio,
    update_orden_servicio,
    assign_orden_servicio,
    iniciar_orden_servicio,
    completar_orden_servicio,
    cancelar_orden_servicio,
)
from app.modules.svc.presentation.schemas import (
    OrdenServicioCreate,
    OrdenServicioUpdate,
    OrdenServicioRead,
)
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()


class OrdenServicioAsignarBody(BaseModel):
    """Cuerpo para asignar técnico (no altera schemas compartidos del módulo)."""

    tecnico_asignado_usuario_id: UUID = Field(..., description="Usuario técnico asignado")


@router.get("", response_model=List[OrdenServicioRead])
async def get_ordenes_servicio(
    empresa_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    cliente_venta_id: Optional[UUID] = Query(None),
    tipo_servicio: Optional[str] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("svc.orden_servicio.leer")),
):
    return await list_orden_servicio(
        current_user.cliente_id,
        empresa_id=empresa_id,
        estado=estado,
        cliente_venta_id=cliente_venta_id,
        tipo_servicio=tipo_servicio,
        buscar=buscar,
    )


@router.get("/{orden_servicio_id}", response_model=OrdenServicioRead)
async def get_orden_servicio(
    orden_servicio_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("svc.orden_servicio.leer")),
):
    try:
        return await get_orden_servicio_by_id(
            current_user.cliente_id,
            orden_servicio_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=OrdenServicioRead, status_code=status.HTTP_201_CREATED)
async def post_orden_servicio(
    data: OrdenServicioCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("svc.orden_servicio.crear")),
):
    return await create_orden_servicio(current_user.cliente_id, data)


@router.put("/{orden_servicio_id}", response_model=OrdenServicioRead)
async def put_orden_servicio(
    orden_servicio_id: UUID,
    data: OrdenServicioUpdate,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("svc.orden_servicio.actualizar")),
):
    try:
        return await update_orden_servicio(
            current_user.cliente_id,
            orden_servicio_id,
            data,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{orden_servicio_id}/asignar", response_model=OrdenServicioRead)
async def post_orden_servicio_asignar(
    orden_servicio_id: UUID,
    body: OrdenServicioAsignarBody,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("svc.orden_servicio.actualizar")),
):
    try:
        return await assign_orden_servicio(
            current_user.cliente_id,
            orden_servicio_id,
            body.tecnico_asignado_usuario_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{orden_servicio_id}/iniciar", response_model=OrdenServicioRead)
async def post_orden_servicio_iniciar(
    orden_servicio_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("svc.orden_servicio.actualizar")),
):
    try:
        return await iniciar_orden_servicio(
            current_user.cliente_id,
            orden_servicio_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{orden_servicio_id}/completar", response_model=OrdenServicioRead)
async def post_orden_servicio_completar(
    orden_servicio_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("svc.orden_servicio.actualizar")),
):
    try:
        return await completar_orden_servicio(
            current_user.cliente_id,
            orden_servicio_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{orden_servicio_id}/cancelar", response_model=OrdenServicioRead)
async def post_orden_servicio_cancelar(
    orden_servicio_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("svc.orden_servicio.cancelar")),
):
    try:
        return await cancelar_orden_servicio(
            current_user.cliente_id,
            orden_servicio_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
