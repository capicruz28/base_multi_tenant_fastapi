"""Endpoints mnt_orden_trabajo."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mnt.application.services import (
    list_orden_trabajo,
    get_orden_trabajo_by_id,
    create_orden_trabajo,
    update_orden_trabajo,
    programar_orden_trabajo,
    iniciar_orden_trabajo,
    pausar_orden_trabajo,
    reanudar_orden_trabajo,
    completar_orden_trabajo,
    cancelar_orden_trabajo,
    cerrar_orden_trabajo,
)
from app.modules.mnt.presentation.schemas import (
    OrdenTrabajoCreate,
    OrdenTrabajoUpdate,
    OrdenTrabajoRead,
    OrdenTrabajoProgramarRequest,
    OrdenTrabajoIniciarRequest,
    OrdenTrabajoCompletarRequest,
    OrdenTrabajoCancelarRequest,
    OrdenTrabajoCerrarRequest,
)
from app.core.exceptions import NotFoundError, ConflictError

MODULE_CODE = "mnt"
RESOURCE_CODE = "orden_trabajo"

router = APIRouter()


@router.get("", response_model=List[OrdenTrabajoRead], tags=["MNT - Órdenes de Trabajo"])
async def get_ordenes_trabajo(
    empresa_id: Optional[UUID] = Query(None),
    activo_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    tipo_mantenimiento: Optional[str] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    return await list_orden_trabajo(
        current_user.cliente_id,
        empresa_id=empresa_id,
        activo_id=activo_id,
        estado=estado,
        tipo_mantenimiento=tipo_mantenimiento,
        buscar=buscar,
    )


@router.get("/{orden_trabajo_id}", response_model=OrdenTrabajoRead, tags=["MNT - Órdenes de Trabajo"])
async def get_orden_trabajo(
    orden_trabajo_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    try:
        return await get_orden_trabajo_by_id(current_user.cliente_id, orden_trabajo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=OrdenTrabajoRead, status_code=status.HTTP_201_CREATED, tags=["MNT - Órdenes de Trabajo"])
async def post_orden_trabajo(
    data: OrdenTrabajoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    return await create_orden_trabajo(current_user.cliente_id, data)


@router.put("/{orden_trabajo_id}", response_model=OrdenTrabajoRead, tags=["MNT - Órdenes de Trabajo"])
async def put_orden_trabajo(
    orden_trabajo_id: UUID,
    data: OrdenTrabajoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    try:
        return await update_orden_trabajo(current_user.cliente_id, orden_trabajo_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# ==========================================================================
# Transiciones de estado (workflow):
#     solicitada -> programada -> en_proceso -> completada -> cerrada
#                                  ^   |
#                                  |   v
#                                pausada
#     Cancelar: cualquier estado salvo cerrada/cancelada -> cancelada
# ==========================================================================
@router.patch(
    "/{orden_trabajo_id}/programar",
    response_model=OrdenTrabajoRead,
    tags=["MNT - Órdenes de Trabajo"],
)
async def patch_programar_orden_trabajo(
    orden_trabajo_id: UUID,
    body: Optional[OrdenTrabajoProgramarRequest] = Body(default=None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.programar")),
):
    """Transición `solicitada` -> `programada`."""
    payload = body or OrdenTrabajoProgramarRequest()
    try:
        return await programar_orden_trabajo(
            current_user.cliente_id,
            orden_trabajo_id,
            fecha_programada=payload.fecha_programada,
            tecnico_asignado_usuario_id=payload.tecnico_asignado_usuario_id,
            tecnico_nombre=payload.tecnico_nombre,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch(
    "/{orden_trabajo_id}/iniciar",
    response_model=OrdenTrabajoRead,
    tags=["MNT - Órdenes de Trabajo"],
)
async def patch_iniciar_orden_trabajo(
    orden_trabajo_id: UUID,
    body: Optional[OrdenTrabajoIniciarRequest] = Body(default=None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.iniciar")),
):
    """Transición `programada` -> `en_proceso`. Setea `fecha_inicio_real` (default = ahora)."""
    payload = body or OrdenTrabajoIniciarRequest()
    try:
        return await iniciar_orden_trabajo(
            current_user.cliente_id,
            orden_trabajo_id,
            fecha_inicio_real=payload.fecha_inicio_real,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch(
    "/{orden_trabajo_id}/pausar",
    response_model=OrdenTrabajoRead,
    tags=["MNT - Órdenes de Trabajo"],
)
async def patch_pausar_orden_trabajo(
    orden_trabajo_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.pausar")),
):
    """Transición `en_proceso` -> `pausada`."""
    try:
        return await pausar_orden_trabajo(current_user.cliente_id, orden_trabajo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch(
    "/{orden_trabajo_id}/reanudar",
    response_model=OrdenTrabajoRead,
    tags=["MNT - Órdenes de Trabajo"],
)
async def patch_reanudar_orden_trabajo(
    orden_trabajo_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.reanudar")),
):
    """Transición `pausada` -> `en_proceso`."""
    try:
        return await reanudar_orden_trabajo(current_user.cliente_id, orden_trabajo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch(
    "/{orden_trabajo_id}/completar",
    response_model=OrdenTrabajoRead,
    tags=["MNT - Órdenes de Trabajo"],
)
async def patch_completar_orden_trabajo(
    orden_trabajo_id: UUID,
    body: Optional[OrdenTrabajoCompletarRequest] = Body(default=None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.completar")),
):
    """Transición `en_proceso` -> `completada`. Setea `fecha_fin_real` (default = ahora)."""
    payload = body or OrdenTrabajoCompletarRequest()
    try:
        return await completar_orden_trabajo(
            current_user.cliente_id,
            orden_trabajo_id,
            fecha_fin_real=payload.fecha_fin_real,
            trabajo_realizado=payload.trabajo_realizado,
            repuestos_utilizados=payload.repuestos_utilizados,
            costo_mano_obra=payload.costo_mano_obra,
            costo_repuestos=payload.costo_repuestos,
            costo_servicios_terceros=payload.costo_servicios_terceros,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch(
    "/{orden_trabajo_id}/cancelar",
    response_model=OrdenTrabajoRead,
    tags=["MNT - Órdenes de Trabajo"],
)
async def patch_cancelar_orden_trabajo(
    orden_trabajo_id: UUID,
    body: Optional[OrdenTrabajoCancelarRequest] = Body(default=None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.cancelar")),
):
    """Transición a `cancelada` desde cualquier estado salvo `cerrada`/`cancelada`."""
    payload = body or OrdenTrabajoCancelarRequest()
    try:
        return await cancelar_orden_trabajo(
            current_user.cliente_id,
            orden_trabajo_id,
            observaciones=payload.observaciones,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch(
    "/{orden_trabajo_id}/cerrar",
    response_model=OrdenTrabajoRead,
    tags=["MNT - Órdenes de Trabajo"],
)
async def patch_cerrar_orden_trabajo(
    orden_trabajo_id: UUID,
    body: Optional[OrdenTrabajoCerrarRequest] = Body(default=None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.cerrar")),
):
    """Transición transaccional `completada` -> `cerrada`.

    Operaciones atómicas (BEGIN / COMMIT / ROLLBACK):
        1. UPDATE mnt_orden_trabajo (estado=cerrada, fecha_cierre, cerrado_por_usuario_id, calificacion_trabajo)
        2. INSERT mnt_historial_mantenimiento (bitácora derivada con costos consolidados)
        3. UPDATE mnt_plan_mantenimiento (fecha_ultimo / fecha_proximo) si plan_mantenimiento_id no es nulo
    Si `cerrado_por_usuario_id` no se envía, se usa el usuario autenticado.
    """
    payload = body or OrdenTrabajoCerrarRequest()
    cerrado_por = payload.cerrado_por_usuario_id or getattr(current_user, "usuario_id", None)
    try:
        return await cerrar_orden_trabajo(
            current_user.cliente_id,
            orden_trabajo_id,
            cerrado_por_usuario_id=cerrado_por,
            calificacion_trabajo=payload.calificacion_trabajo,
            observaciones_historial=payload.observaciones_historial,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
