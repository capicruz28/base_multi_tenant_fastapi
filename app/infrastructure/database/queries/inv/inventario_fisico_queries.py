"""
Queries SQLAlchemy Core para inv_inventario_fisico.
Filtro tenant estricto: todas las operaciones usan cliente_id.
Aislamiento empresa: get/update/list por empresa_id (INV).
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import (
    InvInventarioFisicoTable,
    InvInventarioFisicoDetalleTable,
)
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions

_COLUMNS = {c.name for c in InvInventarioFisicoTable.c}


async def list_inventarios_fisicos(
    client_id: UUID,
    empresa_id: UUID,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Lista inventarios físicos del tenant y empresa."""
    query = select(InvInventarioFisicoTable).where(
        and_(
            InvInventarioFisicoTable.c.cliente_id == client_id,
            InvInventarioFisicoTable.c.empresa_id == empresa_id,
        )
    )
    if almacen_id:
        query = query.where(InvInventarioFisicoTable.c.almacen_id == almacen_id)
    if estado:
        query = query.where(InvInventarioFisicoTable.c.estado == estado)
    if fecha_desde:
        query = query.where(InvInventarioFisicoTable.c.fecha_inventario >= fecha_desde)
    if fecha_hasta:
        query = query.where(InvInventarioFisicoTable.c.fecha_inventario <= fecha_hasta)
    query = query.order_by(InvInventarioFisicoTable.c.fecha_inventario.desc())
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
    payload["fecha_actualizacion"] = datetime.utcnow()
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
