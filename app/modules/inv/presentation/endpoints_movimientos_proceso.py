"""Endpoints INV - Acciones de proceso sobre movimientos."""
from fastapi import APIRouter, Depends, HTTPException, Body
from uuid import UUID

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.application.services import movimiento_proceso_service
from app.modules.inv.presentation.schemas import MovimientoRead
from app.modules.inv.presentation.schemas_proceso import MotivoAnulacion
from app.core.exceptions import NotFoundError, AuthorizationError

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "movimiento"


@router.post(
    "/{movimiento_id}/procesar",
    response_model=MovimientoRead,
    summary="Procesar movimiento (actualiza stock)",
)
async def procesar_movimiento(
    movimiento_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.procesar")
    ),
):
    """Procesa un movimiento de la empresa activa en sesión."""
    client_id = current_user.cliente_id
    try:
        return await movimiento_proceso_service.procesar_movimiento_servicio(
            client_id=client_id,
            movimiento_id=movimiento_id,
            usuario_procesado_id=current_user.usuario_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{movimiento_id}/autorizar",
    response_model=MovimientoRead,
    summary="Autorizar movimiento",
)
async def autorizar_movimiento(
    movimiento_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.autorizar")
    ),
):
    """Autoriza un movimiento de la empresa activa en sesión."""
    client_id = current_user.cliente_id
    try:
        return await movimiento_proceso_service.autorizar_movimiento_servicio(
            client_id=client_id,
            movimiento_id=movimiento_id,
            usuario_autorizado_id=current_user.usuario_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{movimiento_id}/anular",
    response_model=MovimientoRead,
    summary="Anular movimiento (solo si no está procesado)",
)
async def anular_movimiento(
    movimiento_id: UUID,
    payload: MotivoAnulacion = Body(MotivoAnulacion()),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.anular")
    ),
):
    """Anula un movimiento de la empresa activa en sesión."""
    client_id = current_user.cliente_id
    try:
        return await movimiento_proceso_service.anular_movimiento_servicio(
            client_id=client_id,
            movimiento_id=movimiento_id,
            motivo=payload.motivo,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except AuthorizationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
