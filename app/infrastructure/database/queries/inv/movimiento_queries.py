"""
Queries SQLAlchemy Core para inv_movimiento.
Filtro tenant estricto: todas las operaciones usan cliente_id.
Aislamiento empresa: get/update/list por empresa_id (INV).
"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_, or_, func

from app.infrastructure.database.tables_erp import InvMovimientoTable, InvMovimientoDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions
from app.shared.pagination.query_helpers import apply_erp_pagination, apply_erp_sort, extract_count

if TYPE_CHECKING:
    from app.shared.pagination.params import ErpPaginationParams

_COLUMNS = {c.name for c in InvMovimientoTable.c}

_SORT_COLUMNS_MOVIMIENTO = frozenset(
    {"numero_movimiento", "fecha_movimiento", "fecha_contable", "estado", "fecha_creacion"}
)
_SORT_COLUMN_MAP = {
    "numero_movimiento": InvMovimientoTable.c.numero_movimiento,
    "fecha_movimiento": InvMovimientoTable.c.fecha_movimiento,
    "fecha_contable": InvMovimientoTable.c.fecha_contable,
    "estado": InvMovimientoTable.c.estado,
    "fecha_creacion": InvMovimientoTable.c.fecha_creacion,
}
_DEFAULT_MOVIMIENTO_ORDER = [(InvMovimientoTable.c.fecha_movimiento, "desc")]
_MOVIMIENTO_COLUMN_DIR_defaults = {"fecha_movimiento": "desc"}


def _build_movimiento_list_conditions(
    client_id: UUID,
    empresa_id: UUID,
    tipo_movimiento_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> list:
    """Condiciones WHERE compartidas entre COUNT y LIST."""
    conditions = [
        InvMovimientoTable.c.cliente_id == client_id,
        InvMovimientoTable.c.empresa_id == empresa_id,
    ]
    if tipo_movimiento_id:
        conditions.append(InvMovimientoTable.c.tipo_movimiento_id == tipo_movimiento_id)
    if almacen_id:
        conditions.append(
            or_(
                InvMovimientoTable.c.almacen_origen_id == almacen_id,
                InvMovimientoTable.c.almacen_destino_id == almacen_id,
            )
        )
    if estado:
        conditions.append(InvMovimientoTable.c.estado == estado)
    if fecha_desde:
        conditions.append(InvMovimientoTable.c.fecha_movimiento >= fecha_desde)
    if fecha_hasta:
        conditions.append(InvMovimientoTable.c.fecha_movimiento <= fecha_hasta)
    return conditions


def _extract_count(result: List[Dict[str, Any]]) -> int:
    return extract_count(result)


async def count_movimientos(
    client_id: UUID,
    empresa_id: UUID,
    tipo_movimiento_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> int:
    """Cuenta movimientos con los mismos filtros que list_movimientos."""
    conditions = _build_movimiento_list_conditions(
        client_id,
        empresa_id,
        tipo_movimiento_id=tipo_movimiento_id,
        almacen_id=almacen_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    query = select(func.count()).select_from(InvMovimientoTable).where(and_(*conditions))
    result = await execute_query(query, client_id=client_id)
    return _extract_count(result)


async def list_movimientos(
    client_id: UUID,
    empresa_id: UUID,
    tipo_movimiento_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    pagination: Optional["ErpPaginationParams"] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista movimientos del tenant y empresa."""
    conditions = _build_movimiento_list_conditions(
        client_id,
        empresa_id,
        tipo_movimiento_id=tipo_movimiento_id,
        almacen_id=almacen_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    query = select(InvMovimientoTable).where(and_(*conditions))
    query = apply_erp_sort(
        query,
        allowed_columns=_SORT_COLUMNS_MOVIMIENTO,
        column_map=_SORT_COLUMN_MAP,
        sort_by=sort_by,
        sort_dir=sort_dir,
        default_order=_DEFAULT_MOVIMIENTO_ORDER,
        tie_breaker=("movimiento_id", InvMovimientoTable.c.movimiento_id),
        column_dir_defaults=_MOVIMIENTO_COLUMN_DIR_defaults,
    )
    if pagination is not None and pagination.is_paginated:
        query = apply_erp_pagination(query, pagination)
    return await execute_query(query, client_id=client_id)


async def get_movimiento_by_id(
    client_id: UUID,
    movimiento_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene un movimiento por id. Con empresa_id: triple filtro (INV)."""
    conds = [
        InvMovimientoTable.c.cliente_id == client_id,
        InvMovimientoTable.c.movimiento_id == movimiento_id,
    ]
    if empresa_id is not None:
        conds.append(InvMovimientoTable.c.empresa_id == empresa_id)
    query = select(InvMovimientoTable).where(and_(*conds))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_movimiento(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un movimiento. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("movimiento_id", uuid4())
    empresa_id = payload["empresa_id"]
    stmt = insert(InvMovimientoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_movimiento_by_id(
        client_id, payload["movimiento_id"], empresa_id=empresa_id
    )


async def update_movimiento(
    client_id: UUID,
    movimiento_id: UUID,
    data: Dict[str, Any],
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza un movimiento. WHERE: cliente_id + empresa_id + movimiento_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS and k not in ("movimiento_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_movimiento_by_id(client_id, movimiento_id, empresa_id=empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(InvMovimientoTable)
        .where(
            empresa_scoped_conditions(
                InvMovimientoTable,
                client_id=client_id,
                empresa_id=empresa_id,
                entity_id_column=InvMovimientoTable.c.movimiento_id,
                entity_id=movimiento_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_movimiento_by_id(client_id, movimiento_id, empresa_id=empresa_id)


async def get_movimiento_con_detalles(
    client_id: UUID,
    movimiento_id: UUID,
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """
    Retorna cabecera + detalles de la empresa indicada.
    Retorna None si la cabecera no existe para ese tenant/empresa.
    """
    cabecera = await get_movimiento_by_id(
        client_id, movimiento_id, empresa_id=empresa_id
    )
    if not cabecera:
        return None

    query_detalles = (
        select(InvMovimientoDetalleTable)
        .where(
            and_(
                InvMovimientoDetalleTable.c.cliente_id == client_id,
                InvMovimientoDetalleTable.c.empresa_id == empresa_id,
                InvMovimientoDetalleTable.c.movimiento_id == movimiento_id,
            )
        )
        .order_by(InvMovimientoDetalleTable.c.fecha_creacion)
    )
    detalles = await execute_query(query_detalles, client_id=client_id)

    return {**cabecera, "detalles": detalles}
