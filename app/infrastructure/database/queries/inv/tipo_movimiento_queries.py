"""
Queries SQLAlchemy Core para inv_tipo_movimiento.
Filtro tenant estricto: todas las operaciones usan cliente_id.
Aislamiento empresa: get/update/list por empresa_id cuando se provee (INV).
"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_, func

from app.infrastructure.database.tables_erp import InvTipoMovimientoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions
from app.shared.pagination.query_helpers import apply_erp_pagination, apply_erp_sort, extract_count

if TYPE_CHECKING:
    from app.shared.pagination.params import ErpPaginationParams

_COLUMNS = {c.name for c in InvTipoMovimientoTable.c}

_SORT_COLUMNS_TIPO_MOVIMIENTO = frozenset({"codigo", "nombre", "clase_movimiento", "fecha_creacion"})
_SORT_COLUMN_MAP = {
    "codigo": InvTipoMovimientoTable.c.codigo,
    "nombre": InvTipoMovimientoTable.c.nombre,
    "clase_movimiento": InvTipoMovimientoTable.c.clase_movimiento,
    "fecha_creacion": InvTipoMovimientoTable.c.fecha_creacion,
}
_DEFAULT_TIPO_MOVIMIENTO_ORDER = [(InvTipoMovimientoTable.c.nombre, "asc")]


def _build_tipo_movimiento_list_conditions(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> list:
    conditions = [
        InvTipoMovimientoTable.c.cliente_id == client_id,
        InvTipoMovimientoTable.c.empresa_id == empresa_id,
    ]
    if solo_activos:
        conditions.append(InvTipoMovimientoTable.c.es_activo == True)
    if buscar:
        conditions.append(
            or_(
                InvTipoMovimientoTable.c.nombre.ilike(f"%{buscar}%"),
                InvTipoMovimientoTable.c.codigo.ilike(f"%{buscar}%"),
            )
        )
    return conditions


async def count_tipos_movimiento(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> int:
    conditions = _build_tipo_movimiento_list_conditions(
        client_id, empresa_id, solo_activos, buscar
    )
    query = select(func.count()).select_from(InvTipoMovimientoTable).where(
        and_(*conditions)
    )
    result = await execute_query(query, client_id=client_id)
    return extract_count(result)


async def list_tipos_movimiento(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    pagination: Optional["ErpPaginationParams"] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista tipos de movimiento del tenant y empresa."""
    conditions = _build_tipo_movimiento_list_conditions(
        client_id, empresa_id, solo_activos, buscar
    )
    query = select(InvTipoMovimientoTable).where(and_(*conditions))
    query = apply_erp_sort(
        query,
        allowed_columns=_SORT_COLUMNS_TIPO_MOVIMIENTO,
        column_map=_SORT_COLUMN_MAP,
        sort_by=sort_by,
        sort_dir=sort_dir,
        default_order=_DEFAULT_TIPO_MOVIMIENTO_ORDER,
        tie_breaker=("tipo_movimiento_id", InvTipoMovimientoTable.c.tipo_movimiento_id),
    )
    if pagination is not None and pagination.is_paginated:
        query = apply_erp_pagination(query, pagination)
    return await execute_query(query, client_id=client_id)


async def get_tipo_movimiento_by_id(
    client_id: UUID,
    tipo_movimiento_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene un tipo de movimiento por id. Con empresa_id: triple filtro (INV)."""
    conds = [
        InvTipoMovimientoTable.c.cliente_id == client_id,
        InvTipoMovimientoTable.c.tipo_movimiento_id == tipo_movimiento_id,
    ]
    if empresa_id is not None:
        conds.append(InvTipoMovimientoTable.c.empresa_id == empresa_id)
    query = select(InvTipoMovimientoTable).where(and_(*conds))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_tipo_movimiento(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un tipo de movimiento. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("tipo_movimiento_id", uuid4())
    empresa_id = payload["empresa_id"]
    stmt = insert(InvTipoMovimientoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_tipo_movimiento_by_id(
        client_id, payload["tipo_movimiento_id"], empresa_id=empresa_id
    )


async def update_tipo_movimiento(
    client_id: UUID,
    tipo_movimiento_id: UUID,
    data: Dict[str, Any],
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza un tipo de movimiento. WHERE: cliente_id + empresa_id + tipo_movimiento_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS and k not in ("tipo_movimiento_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_tipo_movimiento_by_id(
            client_id, tipo_movimiento_id, empresa_id=empresa_id
        )
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(InvTipoMovimientoTable)
        .where(
            empresa_scoped_conditions(
                InvTipoMovimientoTable,
                client_id=client_id,
                empresa_id=empresa_id,
                entity_id_column=InvTipoMovimientoTable.c.tipo_movimiento_id,
                entity_id=tipo_movimiento_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_tipo_movimiento_by_id(
        client_id, tipo_movimiento_id, empresa_id=empresa_id
    )
