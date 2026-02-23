"""
Queries SQLAlchemy Core para pur_proveedor.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import PurProveedorTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PurProveedorTable.c}


async def list_proveedores(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista proveedores del tenant. Siempre filtra por cliente_id."""
    query = select(PurProveedorTable).where(
        PurProveedorTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(PurProveedorTable.c.empresa_id == empresa_id)
    if solo_activos:
        query = query.where(PurProveedorTable.c.es_activo == True)
    if buscar:
        search_filter = or_(
            PurProveedorTable.c.razon_social.ilike(f"%{buscar}%"),
            PurProveedorTable.c.numero_documento.ilike(f"%{buscar}%"),
            PurProveedorTable.c.codigo_proveedor.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(PurProveedorTable.c.razon_social)
    return await execute_query(query, client_id=client_id)


async def get_proveedor_by_id(client_id: UUID, proveedor_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un proveedor por id. Exige cliente_id para no cruzar tenants."""
    query = select(PurProveedorTable).where(
        and_(
            PurProveedorTable.c.cliente_id == client_id,
            PurProveedorTable.c.proveedor_id == proveedor_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_proveedor(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un proveedor. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("proveedor_id", uuid4())
    stmt = insert(PurProveedorTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_proveedor_by_id(client_id, payload["proveedor_id"])


async def update_proveedor(
    client_id: UUID, proveedor_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un proveedor. WHERE incluye cliente_id y proveedor_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("proveedor_id", "cliente_id")
    }
    if not payload:
        return await get_proveedor_by_id(client_id, proveedor_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(PurProveedorTable)
        .where(
            and_(
                PurProveedorTable.c.cliente_id == client_id,
                PurProveedorTable.c.proveedor_id == proveedor_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_proveedor_by_id(client_id, proveedor_id)
