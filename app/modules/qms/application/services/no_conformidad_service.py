"""
Servicios de aplicación para qms_no_conformidad.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.infrastructure.database.queries.qms import (
    list_no_conformidades as _list_no_conformidades,
    get_no_conformidad_by_id as _get_no_conformidad_by_id,
    create_no_conformidad as _create_no_conformidad,
    update_no_conformidad as _update_no_conformidad,
)
from app.modules.qms.presentation.schemas import (
    NoConformidadCreate,
    NoConformidadUpdate,
    NoConformidadRead,
)
from app.core.exceptions import NotFoundError, ConflictError, ValidationError


async def list_no_conformidades(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    origen: Optional[str] = None,
    tipo_nc: Optional[str] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    buscar: Optional[str] = None
) -> List[NoConformidadRead]:
    """Lista no conformidades del tenant."""
    rows = await _list_no_conformidades(
        client_id=client_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        origen=origen,
        tipo_nc=tipo_nc,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )
    return [NoConformidadRead(**row) for row in rows]


async def get_no_conformidad_by_id(client_id: UUID, no_conformidad_id: UUID) -> NoConformidadRead:
    """Obtiene una no conformidad por id."""
    row = await _get_no_conformidad_by_id(client_id, no_conformidad_id)
    if not row:
        raise NotFoundError(f"No conformidad {no_conformidad_id} no encontrada")
    return NoConformidadRead(**row)


async def create_no_conformidad(client_id: UUID, data: NoConformidadCreate) -> NoConformidadRead:
    """Crea una no conformidad."""
    row = await _create_no_conformidad(client_id, data.model_dump(exclude_none=True))
    return NoConformidadRead(**row)


async def update_no_conformidad(
    client_id: UUID, no_conformidad_id: UUID, data: NoConformidadUpdate
) -> NoConformidadRead:
    """Actualiza una no conformidad."""
    # Campos controlados por transiciones (no por PUT genérico)
    if (
        data.fecha_cierre is not None
        or data.cerrado_por_usuario_id is not None
        or data.estado in {"cerrada", "cancelada"}
    ):
        raise ValidationError("No se permite cerrar/cancelar la no conformidad por este endpoint")

    row = await _update_no_conformidad(
        client_id, no_conformidad_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"No conformidad {no_conformidad_id} no encontrada")
    return NoConformidadRead(**row)


async def cerrar_no_conformidad(
    client_id: UUID,
    no_conformidad_id: UUID,
    cerrado_por_usuario_id: UUID,
    fecha_cierre: Optional[datetime] = None,
) -> NoConformidadRead:
    current_row = await _get_no_conformidad_by_id(client_id, no_conformidad_id)
    if not current_row:
        raise NotFoundError(f"No conformidad {no_conformidad_id} no encontrada")
    estado = current_row.get("estado") or "abierta"
    if estado in {"cerrada", "cancelada"}:
        raise ConflictError("La no conformidad ya se encuentra cerrada/cancelada")

    payload = {
        "estado": "cerrada",
        "fecha_cierre": fecha_cierre or datetime.utcnow(),
        "cerrado_por_usuario_id": cerrado_por_usuario_id,
    }
    row = await _update_no_conformidad(client_id, no_conformidad_id, payload)
    if not row:
        raise NotFoundError(f"No conformidad {no_conformidad_id} no encontrada")
    return NoConformidadRead(**row)


async def cancelar_no_conformidad(
    client_id: UUID,
    no_conformidad_id: UUID,
    cerrado_por_usuario_id: UUID,
    fecha_cierre: Optional[datetime] = None,
) -> NoConformidadRead:
    current_row = await _get_no_conformidad_by_id(client_id, no_conformidad_id)
    if not current_row:
        raise NotFoundError(f"No conformidad {no_conformidad_id} no encontrada")
    estado = current_row.get("estado") or "abierta"
    if estado in {"cerrada", "cancelada"}:
        raise ConflictError("La no conformidad ya se encuentra cerrada/cancelada")

    payload = {
        "estado": "cancelada",
        "fecha_cierre": fecha_cierre or datetime.utcnow(),
        "cerrado_por_usuario_id": cerrado_por_usuario_id,
    }
    row = await _update_no_conformidad(client_id, no_conformidad_id, payload)
    if not row:
        raise NotFoundError(f"No conformidad {no_conformidad_id} no encontrada")
    return NoConformidadRead(**row)
