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
from app.core.exceptions import NotFoundError, ConflictError, ValidationError
from datetime import datetime


async def list_tareas(
    client_id: UUID,
    empresa_id: UUID,
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
        empresa_id=empresa_id,
        almacen_id=almacen_id,
        tipo_tarea=tipo_tarea,
        estado=estado,
        asignado_usuario_id=asignado_usuario_id,
        producto_id=producto_id,
        buscar=buscar
    )
    return [TareaRead(**row) for row in rows]


async def get_tarea_by_id(client_id: UUID, empresa_id: UUID, tarea_id: UUID) -> TareaRead:
    """Obtiene una tarea por id. Lanza NotFoundError si no existe."""
    row = await _get_tarea_by_id(client_id, empresa_id, tarea_id)
    if not row:
        raise NotFoundError(f"Tarea {tarea_id} no encontrada")
    return TareaRead(**row)


async def create_tarea(client_id: UUID, data: TareaCreate) -> TareaRead:
    """Crea una tarea."""
    row = await _create_tarea(
        client_id,
        data.empresa_id,
        data.model_dump(exclude_none=True),
    )
    return TareaRead(**row)


async def update_tarea(
    client_id: UUID, empresa_id: UUID, tarea_id: UUID, data: TareaUpdate
) -> TareaRead:
    """
    Actualiza una tarea.

    Regla: solo es editable en estado inicial (pendiente/borrador).
    """
    current = await _get_tarea_by_id(client_id, empresa_id, tarea_id)
    if not current:
        raise NotFoundError(f"Tarea {tarea_id} no encontrada")

    estado_actual = (current.get("estado") or "").lower()
    if estado_actual not in {"pendiente", "borrador"}:
        raise ConflictError(
            detail=f"No se puede editar la tarea en estado '{estado_actual}'. Use acciones de workflow.",
        )

    payload = data.model_dump(exclude_none=True)
    if "estado" in payload:
        raise ValidationError("No se permite cambiar 'estado' por PUT. Use acciones de workflow.")
    if "fecha_inicio" in payload or "fecha_completado" in payload or "fecha_asignacion" in payload:
        raise ValidationError("No se permite modificar fechas de workflow por PUT. Use acciones de workflow.")

    row = await _update_tarea(
        client_id,
        empresa_id,
        tarea_id,
        payload,
    )
    if not row:
        raise NotFoundError(f"Tarea {tarea_id} no encontrada")
    return TareaRead(**row)


async def asignar_tarea(
    client_id: UUID,
    empresa_id: UUID,
    tarea_id: UUID,
    asignado_usuario_id: UUID,
    asignado_nombre: Optional[str] = None,
) -> TareaRead:
    current = await _get_tarea_by_id(client_id, empresa_id, tarea_id)
    if not current:
        raise NotFoundError(f"Tarea {tarea_id} no encontrada")

    estado_actual = (current.get("estado") or "").lower()
    if estado_actual not in {"pendiente", "borrador"}:
        raise ConflictError(detail=f"No se puede asignar desde estado '{estado_actual}'")

    now = datetime.utcnow()
    row = await _update_tarea(
        client_id,
        empresa_id,
        tarea_id,
        {
            "estado": "asignada",
            "asignado_usuario_id": asignado_usuario_id,
            "asignado_nombre": asignado_nombre,
            "fecha_asignacion": now,
        },
    )
    if not row:
        raise NotFoundError(f"Tarea {tarea_id} no encontrada")
    return TareaRead(**row)


async def iniciar_tarea(client_id: UUID, empresa_id: UUID, tarea_id: UUID) -> TareaRead:
    current = await _get_tarea_by_id(client_id, empresa_id, tarea_id)
    if not current:
        raise NotFoundError(f"Tarea {tarea_id} no encontrada")

    estado_actual = (current.get("estado") or "").lower()
    if estado_actual != "asignada":
        raise ConflictError(detail=f"No se puede iniciar desde estado '{estado_actual}'")

    now = datetime.utcnow()
    row = await _update_tarea(
        client_id,
        empresa_id,
        tarea_id,
        {"estado": "en_proceso", "fecha_inicio": now},
    )
    if not row:
        raise NotFoundError(f"Tarea {tarea_id} no encontrada")
    return TareaRead(**row)


async def completar_tarea(client_id: UUID, empresa_id: UUID, tarea_id: UUID) -> TareaRead:
    current = await _get_tarea_by_id(client_id, empresa_id, tarea_id)
    if not current:
        raise NotFoundError(f"Tarea {tarea_id} no encontrada")

    estado_actual = (current.get("estado") or "").lower()
    if estado_actual != "en_proceso":
        raise ConflictError(detail=f"No se puede completar desde estado '{estado_actual}'")

    now = datetime.utcnow()
    row = await _update_tarea(
        client_id,
        empresa_id,
        tarea_id,
        {"estado": "completada", "fecha_completado": now},
    )
    if not row:
        raise NotFoundError(f"Tarea {tarea_id} no encontrada")
    return TareaRead(**row)


async def cancelar_tarea(client_id: UUID, empresa_id: UUID, tarea_id: UUID) -> TareaRead:
    current = await _get_tarea_by_id(client_id, empresa_id, tarea_id)
    if not current:
        raise NotFoundError(f"Tarea {tarea_id} no encontrada")

    estado_actual = (current.get("estado") or "").lower()
    if estado_actual in {"completada", "cancelada"}:
        raise ConflictError(detail=f"No se puede cancelar desde estado '{estado_actual}'")
    if estado_actual not in {"pendiente", "borrador", "asignada", "en_proceso"}:
        raise ConflictError(detail=f"No se puede cancelar desde estado '{estado_actual}'")

    row = await _update_tarea(
        client_id,
        empresa_id,
        tarea_id,
        {"estado": "cancelada"},
    )
    if not row:
        raise NotFoundError(f"Tarea {tarea_id} no encontrada")
    return TareaRead(**row)
