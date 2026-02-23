"""
Queries SQLAlchemy Core para sls_cliente.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import SlsClienteTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in SlsClienteTable.c}


async def list_clientes(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    vendedor_usuario_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """Lista clientes del tenant. Siempre filtra por cliente_id."""
    query = select(SlsClienteTable).where(
        SlsClienteTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(SlsClienteTable.c.empresa_id == empresa_id)
    if solo_activos:
        query = query.where(SlsClienteTable.c.es_activo == True)
    if buscar:
        search_filter = or_(
            SlsClienteTable.c.razon_social.ilike(f"%{buscar}%"),
            SlsClienteTable.c.numero_documento.ilike(f"%{buscar}%"),
            SlsClienteTable.c.codigo_cliente.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    if vendedor_usuario_id:
        query = query.where(SlsClienteTable.c.vendedor_usuario_id == vendedor_usuario_id)
    query = query.order_by(SlsClienteTable.c.razon_social)
    return await execute_query(query, client_id=client_id)


async def get_cliente_by_id(client_id: UUID, cliente_venta_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un cliente por id. Exige cliente_id para no cruzar tenants."""
    query = select(SlsClienteTable).where(
        and_(
            SlsClienteTable.c.cliente_id == client_id,
            SlsClienteTable.c.cliente_venta_id == cliente_venta_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_cliente(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un cliente. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("cliente_venta_id", uuid4())
    stmt = insert(SlsClienteTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_cliente_by_id(client_id, payload["cliente_venta_id"])


async def update_cliente(
    client_id: UUID, cliente_venta_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un cliente. WHERE incluye cliente_id y cliente_venta_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("cliente_venta_id", "cliente_id")
    }
    if not payload:
        return await get_cliente_by_id(client_id, cliente_venta_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(SlsClienteTable)
        .where(
            and_(
                SlsClienteTable.c.cliente_id == client_id,
                SlsClienteTable.c.cliente_venta_id == cliente_venta_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_cliente_by_id(client_id, cliente_venta_id)
