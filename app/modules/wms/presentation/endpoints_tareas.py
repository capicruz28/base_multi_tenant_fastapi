"""
Endpoints FastAPI para wms_tarea.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.wms.application.services import (
    list_tareas,
    get_tarea_by_id,
    create_tarea,
    update_tarea,
)
from app.modules.wms.presentation.schemas import (
    TareaCreate,
    TareaUpdate,
    TareaRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[TareaRead], tags=["WMS - Tareas"])
async def get_tareas(
    almacen_id: Optional[UUID] = Query(None),
    tipo_tarea: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    asignado_usuario_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista tareas de almacén del tenant."""
    return await list_tareas(
        client_id=current_user.cliente_id,
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
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una tarea por id."""
    try:
        return await get_tarea_by_id(current_user.cliente_id, tarea_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=TareaRead, status_code=status.HTTP_201_CREATED, tags=["WMS - Tareas"])
async def post_tarea(
    data: TareaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una tarea."""
    return await create_tarea(current_user.cliente_id, data)


@router.put("/{tarea_id}", response_model=TareaRead, tags=["WMS - Tareas"])
async def put_tarea(
    tarea_id: UUID,
    data: TareaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una tarea."""
    try:
        return await update_tarea(current_user.cliente_id, tarea_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
