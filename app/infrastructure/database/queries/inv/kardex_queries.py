"""
Queries de Kardex (consulta) basadas en inv_movimiento + inv_movimiento_detalle.
Filtro tenant estricto: cliente_id. Aislamiento empresa: empresa_id obligatorio (INV).
"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import date
from sqlalchemy import select, and_, func

from app.infrastructure.database.tables_erp import InvMovimientoTable, InvMovimientoDetalleTable
from app.infrastructure.database.queries_async import execute_query
from app.shared.pagination.query_helpers import apply_erp_pagination, apply_erp_sort, extract_count

if TYPE_CHECKING:
    from app.shared.pagination.params import ErpPaginationParams

_KARDEX_JOIN = InvMovimientoDetalleTable.join(
    InvMovimientoTable,
    and_(
        InvMovimientoDetalleTable.c.movimiento_id == InvMovimientoTable.c.movimiento_id,
        InvMovimientoDetalleTable.c.cliente_id == InvMovimientoTable.c.cliente_id,
        InvMovimientoDetalleTable.c.empresa_id == InvMovimientoTable.c.empresa_id,
    ),
)

_SORT_COLUMNS_KARDEX = frozenset({"fecha_movimiento", "cantidad_base", "costo_unitario"})
_SORT_COLUMN_MAP = {
    "fecha_movimiento": InvMovimientoTable.c.fecha_movimiento,
    "cantidad_base": InvMovimientoDetalleTable.c.cantidad_base,
    "costo_unitario": InvMovimientoDetalleTable.c.costo_unitario,
}
_DEFAULT_KARDEX_ORDER = [(InvMovimientoTable.c.fecha_movimiento, "desc")]
_KARDEX_COLUMN_DIR_defaults = {"fecha_movimiento": "desc"}


def _build_kardex_conditions(
    client_id: UUID,
    empresa_id: UUID,
    producto_id: UUID,
    almacen_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> list:
    conditions = [
        InvMovimientoTable.c.cliente_id == client_id,
        InvMovimientoTable.c.empresa_id == empresa_id,
        InvMovimientoDetalleTable.c.empresa_id == empresa_id,
        InvMovimientoDetalleTable.c.producto_id == producto_id,
    ]
    if almacen_id:
        conditions.append(
            (InvMovimientoTable.c.almacen_origen_id == almacen_id)
            | (InvMovimientoTable.c.almacen_destino_id == almacen_id)
        )
    if fecha_desde:
        conditions.append(InvMovimientoTable.c.fecha_movimiento >= fecha_desde)
    if fecha_hasta:
        conditions.append(InvMovimientoTable.c.fecha_movimiento <= fecha_hasta)
    return conditions


def _kardex_select_columns():
    return select(
        InvMovimientoTable.c.movimiento_id,
        InvMovimientoDetalleTable.c.movimiento_detalle_id,
        InvMovimientoTable.c.empresa_id,
        InvMovimientoTable.c.fecha_movimiento,
        InvMovimientoTable.c.tipo_movimiento_id,
        InvMovimientoDetalleTable.c.producto_id,
        InvMovimientoTable.c.almacen_origen_id,
        InvMovimientoTable.c.almacen_destino_id,
        InvMovimientoDetalleTable.c.cantidad_base,
        InvMovimientoDetalleTable.c.costo_unitario,
        InvMovimientoDetalleTable.c.moneda_id,
        InvMovimientoDetalleTable.c.lote,
        InvMovimientoDetalleTable.c.numero_serie,
        InvMovimientoDetalleTable.c.observaciones,
    )


async def count_kardex(
    client_id: UUID,
    empresa_id: UUID,
    producto_id: UUID,
    almacen_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> int:
    """Cuenta líneas de kardex con los mismos filtros que list_kardex."""
    conditions = _build_kardex_conditions(
        client_id, empresa_id, producto_id, almacen_id, fecha_desde, fecha_hasta
    )
    query = (
        select(func.count(InvMovimientoDetalleTable.c.movimiento_detalle_id))
        .select_from(_KARDEX_JOIN)
        .where(and_(*conditions))
    )
    result = await execute_query(query, client_id=client_id)
    return extract_count(result)


async def list_kardex(
    client_id: UUID,
    empresa_id: UUID,
    producto_id: UUID,
    almacen_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    pagination: Optional["ErpPaginationParams"] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Devuelve líneas de kardex (movimiento + detalle) de la empresa indicada.
    producto_id es obligatorio (validado en service).
    """
    conditions = _build_kardex_conditions(
        client_id, empresa_id, producto_id, almacen_id, fecha_desde, fecha_hasta
    )
    query = (
        _kardex_select_columns()
        .select_from(_KARDEX_JOIN)
        .where(and_(*conditions))
    )
    query = apply_erp_sort(
        query,
        allowed_columns=_SORT_COLUMNS_KARDEX,
        column_map=_SORT_COLUMN_MAP,
        sort_by=sort_by,
        sort_dir=sort_dir,
        default_order=_DEFAULT_KARDEX_ORDER,
        tie_breaker=("movimiento_detalle_id", InvMovimientoDetalleTable.c.movimiento_detalle_id),
        column_dir_defaults=_KARDEX_COLUMN_DIR_defaults,
    )
    if pagination is not None and pagination.is_paginated:
        query = apply_erp_pagination(query, pagination)
    return await execute_query(query, client_id=client_id)
