"""
Queries SQLAlchemy Core para pur_solicitud_compra_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import PurSolicitudCompraDetalleTable
from app.infrastructure.database.queries_async import (
    execute_query,
    execute_insert,
    execute_update,
)

_COLUMNS = {c.name for c in PurSolicitudCompraDetalleTable.c}
_COMPUTED = frozenset({"total_referencial", "cantidad_pendiente"})
_WRITABLE_COLUMNS = _COLUMNS - _COMPUTED


async def list_solicitudes_detalle(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solicitud_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Lista líneas de solicitudes de compra del tenant. Siempre filtra por cliente_id."""
    query = select(PurSolicitudCompraDetalleTable).where(
        PurSolicitudCompraDetalleTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(PurSolicitudCompraDetalleTable.c.empresa_id == empresa_id)
    if solicitud_id:
        query = query.where(
            PurSolicitudCompraDetalleTable.c.solicitud_id == solicitud_id
        )
    if producto_id:
        query = query.where(PurSolicitudCompraDetalleTable.c.producto_id == producto_id)
    query = query.order_by(
        PurSolicitudCompraDetalleTable.c.solicitud_id,
        PurSolicitudCompraDetalleTable.c.producto_id,
    )
    return await execute_query(query, client_id=client_id)


async def get_solicitud_detalle_by_id(
    client_id: UUID, solicitud_detalle_id: UUID
) -> Optional[Dict[str, Any]]:
    """Obtiene una línea de solicitud de compra por id. Exige cliente_id para no cruzar tenants."""
    query = select(PurSolicitudCompraDetalleTable).where(
        and_(
            PurSolicitudCompraDetalleTable.c.cliente_id == client_id,
            PurSolicitudCompraDetalleTable.c.solicitud_detalle_id == solicitud_detalle_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_solicitud_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una línea de solicitud de compra. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _WRITABLE_COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("solicitud_detalle_id", uuid4())
    stmt = insert(PurSolicitudCompraDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_solicitud_detalle_by_id(client_id, payload["solicitud_detalle_id"])


async def update_solicitud_detalle(
    client_id: UUID, solicitud_detalle_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una línea de solicitud de compra. WHERE incluye cliente_id e id de detalle."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _WRITABLE_COLUMNS
        and k
        not in (
            "solicitud_detalle_id",
            "cliente_id",
        )
    }
    if not payload:
        return await get_solicitud_detalle_by_id(client_id, solicitud_detalle_id)
    stmt = (
        update(PurSolicitudCompraDetalleTable)
        .where(
            and_(
                PurSolicitudCompraDetalleTable.c.cliente_id == client_id,
                PurSolicitudCompraDetalleTable.c.solicitud_detalle_id
                == solicitud_detalle_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_solicitud_detalle_by_id(client_id, solicitud_detalle_id)


