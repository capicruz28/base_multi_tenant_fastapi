"""
Queries SQLAlchemy Core para inv_categoria_producto.
Filtro tenant estricto: todas las operaciones usan cliente_id.
Aislamiento empresa: get/update/list por empresa_id cuando se provee (INV).
"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_, func

from app.infrastructure.database.tables_erp import InvCategoriaProductoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions
from app.shared.pagination.query_helpers import apply_erp_pagination, apply_erp_sort, extract_count

if TYPE_CHECKING:
    from app.shared.pagination.params import ErpPaginationParams

_COLUMNS = {c.name for c in InvCategoriaProductoTable.c}

_SORT_COLUMNS_CATEGORIA = frozenset({"codigo", "nombre", "nivel", "fecha_creacion"})
_SORT_COLUMN_MAP = {
    "codigo": InvCategoriaProductoTable.c.codigo,
    "nombre": InvCategoriaProductoTable.c.nombre,
    "nivel": InvCategoriaProductoTable.c.nivel,
    "fecha_creacion": InvCategoriaProductoTable.c.fecha_creacion,
}
_DEFAULT_CATEGORIA_ORDER = [(InvCategoriaProductoTable.c.nombre, "asc")]


def _build_categoria_list_conditions(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> list:
    conditions = [
        InvCategoriaProductoTable.c.cliente_id == client_id,
        InvCategoriaProductoTable.c.empresa_id == empresa_id,
    ]
    if solo_activos:
        conditions.append(InvCategoriaProductoTable.c.es_activo == True)
    if buscar:
        conditions.append(
            or_(
                InvCategoriaProductoTable.c.nombre.ilike(f"%{buscar}%"),
                InvCategoriaProductoTable.c.codigo.ilike(f"%{buscar}%"),
            )
        )
    return conditions


async def count_categorias(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> int:
    conditions = _build_categoria_list_conditions(
        client_id, empresa_id, solo_activos, buscar
    )
    query = select(func.count()).select_from(InvCategoriaProductoTable).where(
        and_(*conditions)
    )
    result = await execute_query(query, client_id=client_id)
    return extract_count(result)


async def list_categorias(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    pagination: Optional["ErpPaginationParams"] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista categorías del tenant y empresa."""
    conditions = _build_categoria_list_conditions(
        client_id, empresa_id, solo_activos, buscar
    )
    query = select(InvCategoriaProductoTable).where(and_(*conditions))
    query = apply_erp_sort(
        query,
        allowed_columns=_SORT_COLUMNS_CATEGORIA,
        column_map=_SORT_COLUMN_MAP,
        sort_by=sort_by,
        sort_dir=sort_dir,
        default_order=_DEFAULT_CATEGORIA_ORDER,
        tie_breaker=("categoria_id", InvCategoriaProductoTable.c.categoria_id),
    )
    if pagination is not None and pagination.is_paginated:
        query = apply_erp_pagination(query, pagination)
    return await execute_query(query, client_id=client_id)


async def get_categoria_by_id(
    client_id: UUID,
    categoria_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene una categoría por id. Con empresa_id: triple filtro (INV)."""
    conds = [
        InvCategoriaProductoTable.c.cliente_id == client_id,
        InvCategoriaProductoTable.c.categoria_id == categoria_id,
    ]
    if empresa_id is not None:
        conds.append(InvCategoriaProductoTable.c.empresa_id == empresa_id)
    query = select(InvCategoriaProductoTable).where(and_(*conds))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_categoria(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una categoría. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("categoria_id", uuid4())
    empresa_id = payload["empresa_id"]
    stmt = insert(InvCategoriaProductoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_categoria_by_id(
        client_id, payload["categoria_id"], empresa_id=empresa_id
    )


async def update_categoria(
    client_id: UUID,
    categoria_id: UUID,
    data: Dict[str, Any],
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza una categoría. WHERE: cliente_id + empresa_id + categoria_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS and k not in ("categoria_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_categoria_by_id(client_id, categoria_id, empresa_id=empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(InvCategoriaProductoTable)
        .where(
            empresa_scoped_conditions(
                InvCategoriaProductoTable,
                client_id=client_id,
                empresa_id=empresa_id,
                entity_id_column=InvCategoriaProductoTable.c.categoria_id,
                entity_id=categoria_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_categoria_by_id(client_id, categoria_id, empresa_id=empresa_id)
