"""
Servicios de aplicación para wms_tarea.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.wms import (
    list_tareas as _list_tareas,
    get_tarea_by_id as _get_tarea_by_id,
    create_tarea as _create_tarea,
    update_tarea as _update_tarea,
)
from app.modules.wms.presentation.schemas import (
    TareaCreate,
    TareaUpdate,
    TareaRead,
)
from app.core.exceptions import NotFoundError


async def list_tareas(
    client_id: UUID,
    almacen_id: Optional[UUID] = None,
    tipo_tarea: Optional[str] = None,
    estado: Optional[str] = None,
    asignado_usuario_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    buscar: Optional[str] = None
) -> List[TareaRead]:
    """Lista tareas de almacén del tenant."""
    rows = await _list_tareas(
        client_id=client_id,
        almacen_id=almacen_id,
        tipo_tarea=tipo_tarea,
        estado=estado,
        asignado_usuario_id=asignado_usuario_id,
        producto_id=producto_id,
        buscar=buscar
    )
    return [TareaRead(**row) for row in rows]


async def get_tarea_by_id(client_id: UUID, tarea_id: UUID) -> TareaRead:
    """Obtiene una tarea por id. Lanza NotFoundError si no existe."""
    row = await _get_tarea_by_id(client_id, tarea_id)
    if not row:
        raise NotFoundError(f"Tarea {tarea_id} no encontrada")
    return TareaRead(**row)


async def create_tarea(client_id: UUID, data: TareaCreate) -> TareaRead:
    """Crea una tarea."""
    row = await _create_tarea(client_id, data.model_dump(exclude_none=True))
    return TareaRead(**row)


async def update_tarea(
    client_id: UUID, tarea_id: UUID, data: TareaUpdate
) -> TareaRead:
    """Actualiza una tarea. Lanza NotFoundError si no existe."""
    row = await _update_tarea(
        client_id, tarea_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Tarea {tarea_id} no encontrada")
    return TareaRead(**row)
