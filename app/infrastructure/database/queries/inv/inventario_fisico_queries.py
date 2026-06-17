"""
Queries SQLAlchemy Core para inv_inventario_fisico.
Filtro tenant estricto: todas las operaciones usan cliente_id.
Aislamiento empresa: get/update/list por empresa_id (INV).
"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import date
from sqlalchemy import select, insert, update, and_, func

from app.infrastructure.database.tables_erp import (
    InvInventarioFisicoTable,
    InvInventarioFisicoDetalleTable,
)
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions
from app.shared.pagination.query_helpers import apply_erp_pagination, apply_erp_sort, extract_count

if TYPE_CHECKING:
    from app.shared.pagination.params import ErpPaginationParams

_COLUMNS = {c.name for c in InvInventarioFisicoTable.c}

_SORT_COLUMNS_INVENTARIO_FISICO = frozenset(
    {"numero_inventario", "fecha_inventario", "estado", "fecha_creacion"}
)
_SORT_COLUMN_MAP = {
    "numero_inventario": InvInventarioFisicoTable.c.numero_inventario,
    "fecha_inventario": InvInventarioFisicoTable.c.fecha_inventario,
    "estado": InvInventarioFisicoTable.c.estado,
    "fecha_creacion": InvInventarioFisicoTable.c.fecha_creacion,
}
_DEFAULT_INVENTARIO_FISICO_ORDER = [(InvInventarioFisicoTable.c.fecha_inventario, "desc")]
_INVENTARIO_FISICO_COLUMN_DIR_defaults = {"fecha_inventario": "desc"}


def _build_inventario_fisico_list_conditions(
    client_id: UUID,
    empresa_id: UUID,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> list:
    conditions = [
        InvInventarioFisicoTable.c.cliente_id == client_id,
        InvInventarioFisicoTable.c.empresa_id == empresa_id,
    ]
    if almacen_id:
        conditions.append(InvInventarioFisicoTable.c.almacen_id == almacen_id)
    if estado:
        conditions.append(InvInventarioFisicoTable.c.estado == estado)
    if fecha_desde:
        conditions.append(InvInventarioFisicoTable.c.fecha_inventario >= fecha_desde)
    if fecha_hasta:
        conditions.append(InvInventarioFisicoTable.c.fecha_inventario <= fecha_hasta)
    return conditions


async def count_inventarios_fisicos(
    client_id: UUID,
    empresa_id: UUID,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> int:
    conditions = _build_inventario_fisico_list_conditions(
        client_id, empresa_id, almacen_id, estado, fecha_desde, fecha_hasta
    )
    query = select(func.count()).select_from(InvInventarioFisicoTable).where(and_(*conditions))
    result = await execute_query(query, client_id=client_id)
    return extract_count(result)


async def list_inventarios_fisicos(
    client_id: UUID,
    empresa_id: UUID,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    pagination: Optional["ErpPaginationParams"] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista inventarios físicos del tenant y empresa."""
    conditions = _build_inventario_fisico_list_conditions(
        client_id, empresa_id, almacen_id, estado, fecha_desde, fecha_hasta
    )
    query = select(InvInventarioFisicoTable).where(and_(*conditions))
    query = apply_erp_sort(
        query,
        allowed_columns=_SORT_COLUMNS_INVENTARIO_FISICO,
        column_map=_SORT_COLUMN_MAP,
        sort_by=sort_by,
        sort_dir=sort_dir,
        default_order=_DEFAULT_INVENTARIO_FISICO_ORDER,
        tie_breaker=("inventario_fisico_id", InvInventarioFisicoTable.c.inventario_fisico_id),
        column_dir_defaults=_INVENTARIO_FISICO_COLUMN_DIR_defaults,
    )
    if pagination is not None and pagination.is_paginated:
        query = apply_erp_pagination(query, pagination)
    return await execute_query(query, client_id=client_id)


async def get_inventario_fisico_by_id(
    client_id: UUID,
    inventario_fisico_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene un inventario físico por id. Con empresa_id: triple filtro (INV)."""
    conds = [
        InvInventarioFisicoTable.c.cliente_id == client_id,
        InvInventarioFisicoTable.c.inventario_fisico_id == inventario_fisico_id,
    ]
    if empresa_id is not None:
        conds.append(InvInventarioFisicoTable.c.empresa_id == empresa_id)
    query = select(InvInventarioFisicoTable).where(and_(*conds))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_inventario_fisico(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un inventario físico. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("inventario_fisico_id", uuid4())
    empresa_id = payload["empresa_id"]
    stmt = insert(InvInventarioFisicoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_inventario_fisico_by_id(
        client_id, payload["inventario_fisico_id"], empresa_id=empresa_id
    )


async def update_inventario_fisico(
    client_id: UUID,
    inventario_fisico_id: UUID,
    data: Dict[str, Any],
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza un inventario físico. WHERE: cliente_id + empresa_id + inventario_fisico_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS
        and k not in ("inventario_fisico_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_inventario_fisico_by_id(
            client_id, inventario_fisico_id, empresa_id=empresa_id
        )
    stmt = (
        update(InvInventarioFisicoTable)
        .where(
            empresa_scoped_conditions(
                InvInventarioFisicoTable,
                client_id=client_id,
                empresa_id=empresa_id,
                entity_id_column=InvInventarioFisicoTable.c.inventario_fisico_id,
                entity_id=inventario_fisico_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_inventario_fisico_by_id(
        client_id, inventario_fisico_id, empresa_id=empresa_id
    )


async def get_inventario_fisico_con_detalles(
    client_id: UUID,
    inventario_fisico_id: UUID,
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """
    Retorna cabecera + detalles de la empresa indicada.
    Retorna None si la cabecera no existe para ese tenant/empresa.
    """
    cabecera = await get_inventario_fisico_by_id(
        client_id, inventario_fisico_id, empresa_id=empresa_id
    )
    if not cabecera:
        return None

    query_detalles = (
        select(InvInventarioFisicoDetalleTable)
        .where(
            and_(
                InvInventarioFisicoDetalleTable.c.cliente_id == client_id,
                InvInventarioFisicoDetalleTable.c.empresa_id == empresa_id,
                InvInventarioFisicoDetalleTable.c.inventario_fisico_id == inventario_fisico_id,
            )
        )
        .order_by(InvInventarioFisicoDetalleTable.c.producto_id)
    )
    detalles = await execute_query(query_detalles, client_id=client_id)

    return {**cabecera, "detalles": detalles}
