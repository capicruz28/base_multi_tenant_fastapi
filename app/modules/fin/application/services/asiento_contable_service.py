"""
Servicios de aplicación para fin_asiento_contable y fin_asiento_detalle.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.infrastructure.database.queries.fin import (
    list_asientos_contables as _list_asientos_contables,
    get_asiento_contable_by_id as _get_asiento_contable_by_id,
    create_asiento_contable as _create_asiento_contable,
    update_asiento_contable as _update_asiento_contable,
    list_asiento_detalles as _list_asiento_detalles,
    get_asiento_detalle_by_id as _get_asiento_detalle_by_id,
    create_asiento_detalle as _create_asiento_detalle,
    update_asiento_detalle as _update_asiento_detalle,
)
from app.modules.fin.presentation.schemas import (
    AsientoContableCreate,
    AsientoContableUpdate,
    AsientoContableRead,
    AsientoDetalleCreate,
    AsientoDetalleUpdate,
    AsientoDetalleRead,
)
from app.core.exceptions import NotFoundError


async def list_asientos_contables(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    periodo_id: Optional[UUID] = None,
    tipo_asiento: Optional[str] = None,
    estado: Optional[str] = None,
    modulo_origen: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    buscar: Optional[str] = None
) -> List[AsientoContableRead]:
    """Lista asientos contables del tenant."""
    rows = await _list_asientos_contables(
        client_id=client_id,
        empresa_id=empresa_id,
        periodo_id=periodo_id,
        tipo_asiento=tipo_asiento,
        estado=estado,
        modulo_origen=modulo_origen,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )
    return [AsientoContableRead(**row) for row in rows]


async def get_asiento_contable_by_id(client_id: UUID, asiento_id: UUID) -> AsientoContableRead:
    """Obtiene un asiento contable por id. Lanza NotFoundError si no existe."""
    row = await _get_asiento_contable_by_id(client_id, asiento_id)
    if not row:
        raise NotFoundError(f"Asiento contable {asiento_id} no encontrado")
    return AsientoContableRead(**row)


async def create_asiento_contable(client_id: UUID, data: AsientoContableCreate) -> AsientoContableRead:
    """Crea un asiento contable."""
    row = await _create_asiento_contable(client_id, data.model_dump(exclude_none=True))
    return AsientoContableRead(**row)


async def update_asiento_contable(
    client_id: UUID, asiento_id: UUID, data: AsientoContableUpdate
) -> AsientoContableRead:
    """Actualiza un asiento contable. Lanza NotFoundError si no existe."""
    row = await _update_asiento_contable(
        client_id, asiento_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Asiento contable {asiento_id} no encontrado")
    return AsientoContableRead(**row)


# ============================================================================
# DETALLES DE ASIENTO CONTABLE
# ============================================================================

async def list_asiento_detalles(
    client_id: UUID,
    asiento_id: Optional[UUID] = None,
    cuenta_id: Optional[UUID] = None
) -> List[AsientoDetalleRead]:
    """Lista detalles de asiento contable del tenant."""
    rows = await _list_asiento_detalles(
        client_id=client_id,
        asiento_id=asiento_id,
        cuenta_id=cuenta_id
    )
    return [AsientoDetalleRead(**row) for row in rows]


async def get_asiento_detalle_by_id(client_id: UUID, asiento_detalle_id: UUID) -> AsientoDetalleRead:
    """Obtiene un detalle por id. Lanza NotFoundError si no existe."""
    row = await _get_asiento_detalle_by_id(client_id, asiento_detalle_id)
    if not row:
        raise NotFoundError(f"Detalle de asiento contable {asiento_detalle_id} no encontrado")
    return AsientoDetalleRead(**row)


async def create_asiento_detalle(client_id: UUID, data: AsientoDetalleCreate) -> AsientoDetalleRead:
    """Crea un detalle de asiento contable."""
    row = await _create_asiento_detalle(client_id, data.model_dump(exclude_none=True))
    return AsientoDetalleRead(**row)


async def update_asiento_detalle(
    client_id: UUID, asiento_detalle_id: UUID, data: AsientoDetalleUpdate
) -> AsientoDetalleRead:
    """Actualiza un detalle de asiento contable. Lanza NotFoundError si no existe."""
    row = await _update_asiento_detalle(
        client_id, asiento_detalle_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Detalle de asiento contable {asiento_detalle_id} no encontrado")
    return AsientoDetalleRead(**row)
