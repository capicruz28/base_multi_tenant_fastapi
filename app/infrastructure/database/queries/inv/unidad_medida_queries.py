"""
Queries SQLAlchemy Core para inv_unidad_medida.
Filtro tenant estricto: todas las operaciones usan cliente_id.
Aislamiento empresa: get/update/list por empresa_id cuando se provee (INV).
"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_, func

from app.infrastructure.database.tables_erp import InvUnidadMedidaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions
from app.shared.pagination.query_helpers import apply_erp_pagination, apply_erp_sort, extract_count

if TYPE_CHECKING:
    from app.shared.pagination.params import ErpPaginationParams

_COLUMNS = {c.name for c in InvUnidadMedidaTable.c}

_SORT_COLUMNS_UNIDAD_MEDIDA = frozenset({"codigo", "nombre", "tipo_unidad", "fecha_creacion"})
_SORT_COLUMN_MAP = {
    "codigo": InvUnidadMedidaTable.c.codigo,
    "nombre": InvUnidadMedidaTable.c.nombre,
    "tipo_unidad": InvUnidadMedidaTable.c.tipo_unidad,
    "fecha_creacion": InvUnidadMedidaTable.c.fecha_creacion,
}
_DEFAULT_UNIDAD_MEDIDA_ORDER = [(InvUnidadMedidaTable.c.nombre, "asc")]


def _build_unidad_medida_list_conditions(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> list:
    conditions = [
        InvUnidadMedidaTable.c.cliente_id == client_id,
        InvUnidadMedidaTable.c.empresa_id == empresa_id,
    ]
    if solo_activos:
        conditions.append(InvUnidadMedidaTable.c.es_activo == True)
    if buscar:
        conditions.append(
            or_(
                InvUnidadMedidaTable.c.nombre.ilike(f"%{buscar}%"),
                InvUnidadMedidaTable.c.codigo.ilike(f"%{buscar}%"),
            )
        )
    return conditions


async def count_unidades_medida(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> int:
    conditions = _build_unidad_medida_list_conditions(
        client_id, empresa_id, solo_activos, buscar
    )
    query = select(func.count()).select_from(InvUnidadMedidaTable).where(
        and_(*conditions)
    )
    result = await execute_query(query, client_id=client_id)
    return extract_count(result)


async def list_unidades_medida(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    pagination: Optional["ErpPaginationParams"] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista unidades de medida del tenant y empresa."""
    conditions = _build_unidad_medida_list_conditions(
        client_id, empresa_id, solo_activos, buscar
    )
    query = select(InvUnidadMedidaTable).where(and_(*conditions))
    query = apply_erp_sort(
        query,
        allowed_columns=_SORT_COLUMNS_UNIDAD_MEDIDA,
        column_map=_SORT_COLUMN_MAP,
        sort_by=sort_by,
        sort_dir=sort_dir,
        default_order=_DEFAULT_UNIDAD_MEDIDA_ORDER,
        tie_breaker=("unidad_medida_id", InvUnidadMedidaTable.c.unidad_medida_id),
    )
    if pagination is not None and pagination.is_paginated:
        query = apply_erp_pagination(query, pagination)
    return await execute_query(query, client_id=client_id)


async def get_unidad_medida_by_id(
    client_id: UUID,
    unidad_medida_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene una unidad de medida por id. Con empresa_id: triple filtro (INV)."""
    conds = [
        InvUnidadMedidaTable.c.cliente_id == client_id,
        InvUnidadMedidaTable.c.unidad_medida_id == unidad_medida_id,
    ]
    if empresa_id is not None:
        conds.append(InvUnidadMedidaTable.c.empresa_id == empresa_id)
    query = select(InvUnidadMedidaTable).where(and_(*conds))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_unidad_medida(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una unidad de medida. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("unidad_medida_id", uuid4())
    empresa_id = payload["empresa_id"]
    stmt = insert(InvUnidadMedidaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_unidad_medida_by_id(
        client_id, payload["unidad_medida_id"], empresa_id=empresa_id
    )


async def update_unidad_medida(
    client_id: UUID,
    unidad_medida_id: UUID,
    data: Dict[str, Any],
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza una unidad de medida. WHERE: cliente_id + empresa_id + unidad_medida_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS and k not in ("unidad_medida_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_unidad_medida_by_id(
            client_id, unidad_medida_id, empresa_id=empresa_id
        )
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(InvUnidadMedidaTable)
        .where(
            empresa_scoped_conditions(
                InvUnidadMedidaTable,
                client_id=client_id,
                empresa_id=empresa_id,
                entity_id_column=InvUnidadMedidaTable.c.unidad_medida_id,
                entity_id=unidad_medida_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_unidad_medida_by_id(
        client_id, unidad_medida_id, empresa_id=empresa_id
    )
