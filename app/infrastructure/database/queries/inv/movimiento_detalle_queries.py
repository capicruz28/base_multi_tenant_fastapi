"""
Queries SQLAlchemy Core para inv_movimiento_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
Aislamiento empresa: get/update/list por empresa_id (INV).
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import InvMovimientoDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions

_COLUMNS = {c.name for c in InvMovimientoDetalleTable.c}


async def list_movimientos_detalle(
    client_id: UUID,
    empresa_id: UUID,
    movimiento_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Lista líneas de movimientos del tenant y empresa."""
    query = select(InvMovimientoDetalleTable).where(
        and_(
            InvMovimientoDetalleTable.c.cliente_id == client_id,
            InvMovimientoDetalleTable.c.empresa_id == empresa_id,
        )
    )
    if movimiento_id:
        query = query.where(InvMovimientoDetalleTable.c.movimiento_id == movimiento_id)
    if producto_id:
        query = query.where(InvMovimientoDetalleTable.c.producto_id == producto_id)
    query = query.order_by(
        InvMovimientoDetalleTable.c.movimiento_id,
        InvMovimientoDetalleTable.c.fecha_creacion,
    )
    return await execute_query(query, client_id=client_id)


async def get_movimiento_detalle_by_id(
    client_id: UUID,
    movimiento_detalle_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene una línea por id. Con empresa_id: triple filtro (INV)."""
    conds = [
        InvMovimientoDetalleTable.c.cliente_id == client_id,
        InvMovimientoDetalleTable.c.movimiento_detalle_id == movimiento_detalle_id,
    ]
    if empresa_id is not None:
        conds.append(InvMovimientoDetalleTable.c.empresa_id == empresa_id)
    query = select(InvMovimientoDetalleTable).where(and_(*conds))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_movimiento_detalle(
    client_id: UUID, data: Dict[str, Any]
) -> Dict[str, Any]:
    """Inserta una línea de movimiento. cliente_id se fuerza desde contexto."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("movimiento_detalle_id", uuid4())
    empresa_id = payload["empresa_id"]
    stmt = insert(InvMovimientoDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_movimiento_detalle_by_id(
        client_id, payload["movimiento_detalle_id"], empresa_id=empresa_id
    )


async def update_movimiento_detalle(
    client_id: UUID,
    movimiento_detalle_id: UUID,
    data: Dict[str, Any],
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza una línea. WHERE: cliente_id + empresa_id + movimiento_detalle_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS
        and k not in ("movimiento_detalle_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_movimiento_detalle_by_id(
            client_id, movimiento_detalle_id, empresa_id=empresa_id
        )
    stmt = (
        update(InvMovimientoDetalleTable)
        .where(
            empresa_scoped_conditions(
                InvMovimientoDetalleTable,
                client_id=client_id,
                empresa_id=empresa_id,
                entity_id_column=InvMovimientoDetalleTable.c.movimiento_detalle_id,
                entity_id=movimiento_detalle_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_movimiento_detalle_by_id(
        client_id, movimiento_detalle_id, empresa_id=empresa_id
    )
