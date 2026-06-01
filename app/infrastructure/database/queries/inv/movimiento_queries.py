"""
Queries SQLAlchemy Core para inv_movimiento.
Filtro tenant estricto: todas las operaciones usan cliente_id.
Aislamiento empresa: get/update/list por empresa_id (INV).
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import InvMovimientoTable, InvMovimientoDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions

_COLUMNS = {c.name for c in InvMovimientoTable.c}


async def list_movimientos(
    client_id: UUID,
    empresa_id: UUID,
    tipo_movimiento_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Lista movimientos del tenant y empresa."""
    query = select(InvMovimientoTable).where(
        and_(
            InvMovimientoTable.c.cliente_id == client_id,
            InvMovimientoTable.c.empresa_id == empresa_id,
        )
    )
    if tipo_movimiento_id:
        query = query.where(InvMovimientoTable.c.tipo_movimiento_id == tipo_movimiento_id)
    if almacen_id:
        query = query.where(
            or_(
                InvMovimientoTable.c.almacen_origen_id == almacen_id,
                InvMovimientoTable.c.almacen_destino_id == almacen_id,
            )
        )
    if estado:
        query = query.where(InvMovimientoTable.c.estado == estado)
    if fecha_desde:
        query = query.where(InvMovimientoTable.c.fecha_movimiento >= fecha_desde)
    if fecha_hasta:
        query = query.where(InvMovimientoTable.c.fecha_movimiento <= fecha_hasta)
    query = query.order_by(InvMovimientoTable.c.fecha_movimiento.desc())
    return await execute_query(query, client_id=client_id)


async def get_movimiento_by_id(
    client_id: UUID,
    movimiento_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene un movimiento por id. Con empresa_id: triple filtro (INV)."""
    conds = [
        InvMovimientoTable.c.cliente_id == client_id,
        InvMovimientoTable.c.movimiento_id == movimiento_id,
    ]
    if empresa_id is not None:
        conds.append(InvMovimientoTable.c.empresa_id == empresa_id)
    query = select(InvMovimientoTable).where(and_(*conds))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_movimiento(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un movimiento. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("movimiento_id", uuid4())
    empresa_id = payload["empresa_id"]
    stmt = insert(InvMovimientoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_movimiento_by_id(
        client_id, payload["movimiento_id"], empresa_id=empresa_id
    )


async def update_movimiento(
    client_id: UUID,
    movimiento_id: UUID,
    data: Dict[str, Any],
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza un movimiento. WHERE: cliente_id + empresa_id + movimiento_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS and k not in ("movimiento_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_movimiento_by_id(client_id, movimiento_id, empresa_id=empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(InvMovimientoTable)
        .where(
            empresa_scoped_conditions(
                InvMovimientoTable,
                client_id=client_id,
                empresa_id=empresa_id,
                entity_id_column=InvMovimientoTable.c.movimiento_id,
                entity_id=movimiento_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_movimiento_by_id(client_id, movimiento_id, empresa_id=empresa_id)


async def get_movimiento_con_detalles(
    client_id: UUID,
    movimiento_id: UUID,
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """
    Retorna cabecera + detalles de la empresa indicada.
    Retorna None si la cabecera no existe para ese tenant/empresa.
    """
    cabecera = await get_movimiento_by_id(
        client_id, movimiento_id, empresa_id=empresa_id
    )
    if not cabecera:
        return None

    query_detalles = (
        select(InvMovimientoDetalleTable)
        .where(
            and_(
                InvMovimientoDetalleTable.c.cliente_id == client_id,
                InvMovimientoDetalleTable.c.empresa_id == empresa_id,
                InvMovimientoDetalleTable.c.movimiento_id == movimiento_id,
            )
        )
        .order_by(InvMovimientoDetalleTable.c.fecha_creacion)
    )
    detalles = await execute_query(query_detalles, client_id=client_id)

    return {**cabecera, "detalles": detalles}
