"""
Endpoints FastAPI para wms_tarea.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.wms.application.services import (
    list_tareas,
    get_tarea_by_id,
    create_tarea,
    update_tarea,
    asignar_tarea,
    iniciar_tarea,
    completar_tarea,
    cancelar_tarea,
)
from app.modules.wms.presentation.schemas import (
    TareaCreate,
    TareaUpdate,
    TareaRead,
    TareaAsignarRequest,
)
from app.core.exceptions import NotFoundError

MODULE_CODE = "wms"
RESOURCE_CODE = "tarea"

router = APIRouter()


@router.get("", response_model=List[TareaRead], tags=["WMS - Tareas"])
async def get_tareas(
    empresa_id: UUID = Query(...),
    almacen_id: Optional[UUID] = Query(None),
    tipo_tarea: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    asignado_usuario_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista tareas de almacén del tenant."""
    return await list_tareas(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        almacen_id=almacen_id,
        tipo_tarea=tipo_tarea,
        estado=estado,
        asignado_usuario_id=asignado_usuario_id,
        producto_id=producto_id,
        buscar=buscar
    )


@router.get("/{tarea_id}", response_model=TareaRead, tags=["WMS - Tareas"])
async def get_tarea(
    tarea_id: UUID,
    empresa_id: UUID = Query(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission("wms.tarea.leer")),
):
    """Obtiene una tarea por id."""
    try:
        return await get_tarea_by_id(current_user.cliente_id, empresa_id, tarea_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=TareaRead, status_code=status.HTTP_201_CREATED, tags=["WMS - Tareas"])
async def post_tarea(
    data: TareaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una tarea."""
    return await create_tarea(current_user.cliente_id, data)


@router.put("/{tarea_id}", response_model=TareaRead, tags=["WMS - Tareas"])
async def put_tarea(
    tarea_id: UUID,
    data: TareaUpdate,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una tarea."""
    empresa_id_final = data.empresa_id or empresa_id
    if empresa_id_final is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empresa_id es requerido")
    try:
        return await update_tarea(current_user.cliente_id, empresa_id_final, tarea_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{tarea_id}/asignar", response_model=TareaRead, tags=["WMS - Tareas"])
async def post_tarea_asignar(
    tarea_id: UUID,
    empresa_id: UUID = Query(...),
    data: TareaAsignarRequest = ...,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission("wms.tarea.actualizar")),
):
    """Asigna una tarea (pendiente/borrador → asignada)."""
    try:
        return await asignar_tarea(
            current_user.cliente_id,
            empresa_id,
            tarea_id,
            data.asignado_usuario_id,
            data.asignado_nombre,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{tarea_id}/iniciar", response_model=TareaRead, tags=["WMS - Tareas"])
async def post_tarea_iniciar(
    tarea_id: UUID,
    empresa_id: UUID = Query(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission("wms.tarea.actualizar")),
):
    """Inicia una tarea (asignada → en_proceso)."""
    try:
        return await iniciar_tarea(current_user.cliente_id, empresa_id, tarea_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{tarea_id}/completar", response_model=TareaRead, tags=["WMS - Tareas"])
async def post_tarea_completar(
    tarea_id: UUID,
    empresa_id: UUID = Query(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission("wms.tarea.actualizar")),
):
    """Completa una tarea (en_proceso → completada)."""
    try:
        return await completar_tarea(current_user.cliente_id, empresa_id, tarea_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{tarea_id}/cancelar", response_model=TareaRead, tags=["WMS - Tareas"])
async def post_tarea_cancelar(
    tarea_id: UUID,
    empresa_id: UUID = Query(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission("wms.tarea.actualizar")),
):
    """Cancela una tarea (no permitido desde completada/cancelada)."""
    try:
        return await cancelar_tarea(current_user.cliente_id, empresa_id, tarea_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
