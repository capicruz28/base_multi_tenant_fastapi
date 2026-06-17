"""
Queries SQLAlchemy Core para inv_almacen.
Filtro tenant estricto: todas las operaciones usan cliente_id.
Aislamiento empresa: get/update/list por empresa_id cuando se provee (INV).
"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_, func

from app.infrastructure.database.tables_erp import InvAlmacenTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions
from app.shared.pagination.query_helpers import apply_erp_pagination, apply_erp_sort, extract_count

if TYPE_CHECKING:
    from app.shared.pagination.params import ErpPaginationParams

_COLUMNS = {c.name for c in InvAlmacenTable.c}

_SORT_COLUMNS_ALMACEN = frozenset({"codigo", "nombre", "tipo_almacen", "fecha_creacion"})
_SORT_COLUMN_MAP = {
    "codigo": InvAlmacenTable.c.codigo,
    "nombre": InvAlmacenTable.c.nombre,
    "tipo_almacen": InvAlmacenTable.c.tipo_almacen,
    "fecha_creacion": InvAlmacenTable.c.fecha_creacion,
}
_DEFAULT_ALMACEN_ORDER = [(InvAlmacenTable.c.nombre, "asc")]


def _build_almacen_list_conditions(
    client_id: UUID,
    empresa_id: UUID,
    sucursal_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> list:
    conditions = [
        InvAlmacenTable.c.cliente_id == client_id,
        InvAlmacenTable.c.empresa_id == empresa_id,
    ]
    if sucursal_id:
        conditions.append(InvAlmacenTable.c.sucursal_id == sucursal_id)
    if solo_activos:
        conditions.append(InvAlmacenTable.c.es_activo == True)
    if buscar:
        conditions.append(
            or_(
                InvAlmacenTable.c.nombre.ilike(f"%{buscar}%"),
                InvAlmacenTable.c.codigo.ilike(f"%{buscar}%"),
            )
        )
    return conditions


async def count_almacenes(
    client_id: UUID,
    empresa_id: UUID,
    sucursal_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> int:
    conditions = _build_almacen_list_conditions(
        client_id, empresa_id, sucursal_id, solo_activos, buscar
    )
    query = select(func.count()).select_from(InvAlmacenTable).where(and_(*conditions))
    result = await execute_query(query, client_id=client_id)
    return extract_count(result)


async def list_almacenes(
    client_id: UUID,
    empresa_id: UUID,
    sucursal_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    pagination: Optional["ErpPaginationParams"] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista almacenes del tenant y empresa."""
    conditions = _build_almacen_list_conditions(
        client_id, empresa_id, sucursal_id, solo_activos, buscar
    )
    query = select(InvAlmacenTable).where(and_(*conditions))
    query = apply_erp_sort(
        query,
        allowed_columns=_SORT_COLUMNS_ALMACEN,
        column_map=_SORT_COLUMN_MAP,
        sort_by=sort_by,
        sort_dir=sort_dir,
        default_order=_DEFAULT_ALMACEN_ORDER,
        tie_breaker=("almacen_id", InvAlmacenTable.c.almacen_id),
    )
    if pagination is not None and pagination.is_paginated:
        query = apply_erp_pagination(query, pagination)
    return await execute_query(query, client_id=client_id)


async def get_almacen_by_id(
    client_id: UUID,
    almacen_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene un almacén por id. Con empresa_id: triple filtro (INV)."""
    conds = [
        InvAlmacenTable.c.cliente_id == client_id,
        InvAlmacenTable.c.almacen_id == almacen_id,
    ]
    if empresa_id is not None:
        conds.append(InvAlmacenTable.c.empresa_id == empresa_id)
    query = select(InvAlmacenTable).where(and_(*conds))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_almacen(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un almacén. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("almacen_id", uuid4())
    empresa_id = payload["empresa_id"]
    stmt = insert(InvAlmacenTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_almacen_by_id(
        client_id, payload["almacen_id"], empresa_id=empresa_id
    )


async def update_almacen(
    client_id: UUID,
    almacen_id: UUID,
    data: Dict[str, Any],
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza un almacén. WHERE: cliente_id + empresa_id + almacen_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS and k not in ("almacen_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_almacen_by_id(client_id, almacen_id, empresa_id=empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(InvAlmacenTable)
        .where(
            empresa_scoped_conditions(
                InvAlmacenTable,
                client_id=client_id,
                empresa_id=empresa_id,
                entity_id_column=InvAlmacenTable.c.almacen_id,
                entity_id=almacen_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_almacen_by_id(client_id, almacen_id, empresa_id=empresa_id)
