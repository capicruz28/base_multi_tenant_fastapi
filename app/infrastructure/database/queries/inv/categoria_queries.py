"""
Queries SQLAlchemy Core para inv_categoria_producto.
Filtro tenant estricto: todas las operaciones usan cliente_id.
Aislamiento empresa: get/update/list por empresa_id cuando se provee (INV).
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import InvCategoriaProductoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions

_COLUMNS = {c.name for c in InvCategoriaProductoTable.c}


async def list_categorias(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
) -> List[Dict[str, Any]]:
    """Lista categorías del tenant y empresa."""
    query = select(InvCategoriaProductoTable).where(
        and_(
            InvCategoriaProductoTable.c.cliente_id == client_id,
            InvCategoriaProductoTable.c.empresa_id == empresa_id,
        )
    )
    if solo_activos:
        query = query.where(InvCategoriaProductoTable.c.es_activo == True)
    query = query.order_by(InvCategoriaProductoTable.c.nombre)
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
