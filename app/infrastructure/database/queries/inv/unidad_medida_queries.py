"""
Queries SQLAlchemy Core para inv_unidad_medida.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import InvUnidadMedidaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in InvUnidadMedidaTable.c}


async def list_unidades_medida(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True
) -> List[Dict[str, Any]]:
    """Lista unidades de medida del tenant. Siempre filtra por cliente_id."""
    query = select(InvUnidadMedidaTable).where(
        InvUnidadMedidaTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(InvUnidadMedidaTable.c.empresa_id == empresa_id)
    if solo_activos:
        query = query.where(InvUnidadMedidaTable.c.es_activo == True)
    query = query.order_by(InvUnidadMedidaTable.c.nombre)
    return await execute_query(query, client_id=client_id)


async def get_unidad_medida_by_id(client_id: UUID, unidad_medida_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una unidad de medida por id. Exige cliente_id para no cruzar tenants."""
    query = select(InvUnidadMedidaTable).where(
        and_(
            InvUnidadMedidaTable.c.cliente_id == client_id,
            InvUnidadMedidaTable.c.unidad_medida_id == unidad_medida_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_unidad_medida(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una unidad de medida. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("unidad_medida_id", uuid4())
    stmt = insert(InvUnidadMedidaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_unidad_medida_by_id(client_id, payload["unidad_medida_id"])


async def update_unidad_medida(
    client_id: UUID, unidad_medida_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una unidad de medida. WHERE incluye cliente_id y unidad_medida_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("unidad_medida_id", "cliente_id")
    }
    if not payload:
        return await get_unidad_medida_by_id(client_id, unidad_medida_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(InvUnidadMedidaTable)
        .where(
            and_(
                InvUnidadMedidaTable.c.cliente_id == client_id,
                InvUnidadMedidaTable.c.unidad_medida_id == unidad_medida_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_unidad_medida_by_id(client_id, unidad_medida_id)
