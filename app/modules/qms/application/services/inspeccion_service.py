"""
Servicios de aplicación para qms_inspeccion y qms_inspeccion_detalle.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.infrastructure.database.queries.qms import (
    list_inspecciones as _list_inspecciones,
    get_inspeccion_by_id as _get_inspeccion_by_id,
    create_inspeccion as _create_inspeccion,
    update_inspeccion as _update_inspeccion,
    list_inspeccion_detalles as _list_inspeccion_detalles,
    get_inspeccion_detalle_by_id as _get_inspeccion_detalle_by_id,
    create_inspeccion_detalle as _create_inspeccion_detalle,
    update_inspeccion_detalle as _update_inspeccion_detalle,
)
from app.modules.qms.presentation.schemas import (
    InspeccionCreate,
    InspeccionUpdate,
    InspeccionRead,
    InspeccionDetalleCreate,
    InspeccionDetalleUpdate,
    InspeccionDetalleRead,
)
from app.core.exceptions import NotFoundError, ConflictError, ValidationError

_INSPECCION_EDITABLE_RESULTADOS = {"pendiente"}
_INSPECCION_ESTADOS_APROBADO = "aprobado"
_INSPECCION_ESTADOS_PROCESADO = "procesado"
_INSPECCION_ESTADOS_ANULADO = "anulado"


async def list_inspecciones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    plan_inspeccion_id: Optional[UUID] = None,
    resultado: Optional[str] = None,
    lote: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    buscar: Optional[str] = None
) -> List[InspeccionRead]:
    """Lista inspecciones del tenant."""
    rows = await _list_inspecciones(
        client_id=client_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        plan_inspeccion_id=plan_inspeccion_id,
        resultado=resultado,
        lote=lote,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )
    return [InspeccionRead(**row) for row in rows]


async def get_inspeccion_by_id(client_id: UUID, inspeccion_id: UUID) -> InspeccionRead:
    """Obtiene una inspección por id."""
    row = await _get_inspeccion_by_id(client_id, inspeccion_id)
    if not row:
        raise NotFoundError(f"Inspección {inspeccion_id} no encontrada")
    return InspeccionRead(**row)


async def create_inspeccion(client_id: UUID, data: InspeccionCreate) -> InspeccionRead:
    """Crea una inspección."""
    row = await _create_inspeccion(client_id, data.model_dump(exclude_none=True))
    return InspeccionRead(**row)


async def update_inspeccion(
    client_id: UUID, inspeccion_id: UUID, data: InspeccionUpdate
) -> InspeccionRead:
    """Actualiza una inspección."""
    current_row = await _get_inspeccion_by_id(client_id, inspeccion_id)
    if not current_row:
        raise NotFoundError(f"Inspección {inspeccion_id} no encontrada")
    if (current_row.get("resultado") or "pendiente") not in _INSPECCION_EDITABLE_RESULTADOS:
        raise ConflictError("La inspección ya no es editable en su estado actual")

    # Campos controlados por transiciones (no por PUT genérico)
    if data.resultado is not None:
        raise ValidationError("No se permite modificar 'resultado' por este endpoint")
    if data.aprobado_por_usuario_id is not None or data.fecha_aprobacion is not None:
        raise ValidationError("No se permite modificar campos de aprobación por este endpoint")

    row = await _update_inspeccion(
        client_id, inspeccion_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Inspección {inspeccion_id} no encontrada")
    return InspeccionRead(**row)


async def list_inspeccion_detalles(
    client_id: UUID, inspeccion_id: UUID
) -> List[InspeccionDetalleRead]:
    """Lista detalles de una inspección."""
    inspeccion_row = await _get_inspeccion_by_id(client_id, inspeccion_id)
    if not inspeccion_row:
        raise NotFoundError(f"Inspección {inspeccion_id} no encontrada")
    rows = await _list_inspeccion_detalles(
        client_id,
        inspeccion_id,
        empresa_id=inspeccion_row.get("empresa_id"),
    )
    return [InspeccionDetalleRead(**row) for row in rows]


async def get_inspeccion_detalle_by_id(
    client_id: UUID, inspeccion_detalle_id: UUID
) -> InspeccionDetalleRead:
    """Obtiene un detalle por id."""
    row = await _get_inspeccion_detalle_by_id(client_id, inspeccion_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle de inspección {inspeccion_detalle_id} no encontrado")
    return InspeccionDetalleRead(**row)


async def create_inspeccion_detalle(
    client_id: UUID, data: InspeccionDetalleCreate
) -> InspeccionDetalleRead:
    """Crea un detalle de inspección."""
    inspeccion_row = await _get_inspeccion_by_id(client_id, data.inspeccion_id)
    if not inspeccion_row:
        raise NotFoundError(f"Inspección {data.inspeccion_id} no encontrada")
    if (inspeccion_row.get("resultado") or "pendiente") not in _INSPECCION_EDITABLE_RESULTADOS:
        raise ConflictError("No se puede modificar el detalle: la inspección ya no es editable")

    payload = data.model_dump(exclude_none=True)
    payload["empresa_id"] = inspeccion_row.get("empresa_id")
    row = await _create_inspeccion_detalle(client_id, payload)
    return InspeccionDetalleRead(**row)


async def update_inspeccion_detalle(
    client_id: UUID, inspeccion_detalle_id: UUID, data: InspeccionDetalleUpdate
) -> InspeccionDetalleRead:
    """Actualiza un detalle de inspección."""
    current_row = await _get_inspeccion_detalle_by_id(client_id, inspeccion_detalle_id)
    if not current_row:
        raise NotFoundError(f"Detalle de inspección {inspeccion_detalle_id} no encontrado")

    inspeccion_row = await _get_inspeccion_by_id(client_id, current_row["inspeccion_id"])
    if not inspeccion_row:
        raise NotFoundError(f"Inspección {current_row['inspeccion_id']} no encontrada")
    if (inspeccion_row.get("resultado") or "pendiente") not in _INSPECCION_EDITABLE_RESULTADOS:
        raise ConflictError("No se puede modificar el detalle: la inspección ya no es editable")

    row = await _update_inspeccion_detalle(
        client_id, inspeccion_detalle_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Detalle de inspección {inspeccion_detalle_id} no encontrado")
    return InspeccionDetalleRead(**row)


async def aprobar_inspeccion(
    client_id: UUID,
    inspeccion_id: UUID,
    aprobado_por_usuario_id: UUID,
    fecha_aprobacion: Optional[datetime] = None,
) -> InspeccionRead:
    inspeccion_row = await _get_inspeccion_by_id(client_id, inspeccion_id)
    if not inspeccion_row:
        raise NotFoundError(f"Inspección {inspeccion_id} no encontrada")
    if (inspeccion_row.get("resultado") or "pendiente") != "pendiente":
        raise ConflictError("Solo se puede aprobar una inspección en estado pendiente")

    payload = {
        "resultado": _INSPECCION_ESTADOS_APROBADO,
        "aprobado_por_usuario_id": aprobado_por_usuario_id,
        "fecha_aprobacion": fecha_aprobacion or datetime.utcnow(),
    }
    row = await _update_inspeccion(client_id, inspeccion_id, payload)
    if not row:
        raise NotFoundError(f"Inspección {inspeccion_id} no encontrada")
    return InspeccionRead(**row)


async def procesar_inspeccion(client_id: UUID, inspeccion_id: UUID) -> InspeccionRead:
    inspeccion_row = await _get_inspeccion_by_id(client_id, inspeccion_id)
    if not inspeccion_row:
        raise NotFoundError(f"Inspección {inspeccion_id} no encontrada")
    if (inspeccion_row.get("resultado") or "pendiente") != _INSPECCION_ESTADOS_APROBADO:
        raise ConflictError("Solo se puede procesar una inspección aprobada")

    row = await _update_inspeccion(client_id, inspeccion_id, {"resultado": _INSPECCION_ESTADOS_PROCESADO})
    if not row:
        raise NotFoundError(f"Inspección {inspeccion_id} no encontrada")
    return InspeccionRead(**row)


async def anular_inspeccion(client_id: UUID, inspeccion_id: UUID) -> InspeccionRead:
    inspeccion_row = await _get_inspeccion_by_id(client_id, inspeccion_id)
    if not inspeccion_row:
        raise NotFoundError(f"Inspección {inspeccion_id} no encontrada")
    resultado = inspeccion_row.get("resultado") or "pendiente"
    if resultado in {_INSPECCION_ESTADOS_PROCESADO, _INSPECCION_ESTADOS_ANULADO}:
        raise ConflictError("No se puede anular una inspección procesada o ya anulada")

    row = await _update_inspeccion(client_id, inspeccion_id, {"resultado": _INSPECCION_ESTADOS_ANULADO})
    if not row:
        raise NotFoundError(f"Inspección {inspeccion_id} no encontrada")
    return InspeccionRead(**row)
