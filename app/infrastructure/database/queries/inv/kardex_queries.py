"""
Queries de Kardex (consulta) basadas en inv_movimiento + inv_movimiento_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date
from sqlalchemy import select, and_

from app.infrastructure.database.tables_erp import InvMovimientoTable, InvMovimientoDetalleTable
from app.infrastructure.database.queries_async import execute_query


async def list_kardex(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Devuelve líneas de kardex (movimiento + detalle) filtradas.
    Nota: no calcula saldo acumulado; entrega la secuencia de movimientos.
    """
    query = (
        select(
            InvMovimientoTable.c.movimiento_id,
            InvMovimientoDetalleTable.c.movimiento_detalle_id,
            InvMovimientoTable.c.empresa_id,
            InvMovimientoTable.c.fecha_movimiento,
            InvMovimientoTable.c.tipo_movimiento_id,
            InvMovimientoDetalleTable.c.producto_id,
            InvMovimientoTable.c.almacen_origen_id,
            InvMovimientoTable.c.almacen_destino_id,
            InvMovimientoDetalleTable.c.cantidad_base,
            InvMovimientoDetalleTable.c.costo_unitario,
            InvMovimientoDetalleTable.c.moneda,
            InvMovimientoDetalleTable.c.lote,
            InvMovimientoDetalleTable.c.numero_serie,
            InvMovimientoDetalleTable.c.observaciones,
        )
        .select_from(
            InvMovimientoDetalleTable.join(
                InvMovimientoTable,
                and_(
                    InvMovimientoDetalleTable.c.movimiento_id
                    == InvMovimientoTable.c.movimiento_id,
                    InvMovimientoDetalleTable.c.cliente_id
                    == InvMovimientoTable.c.cliente_id,
                ),
            )
        )
        .where(InvMovimientoTable.c.cliente_id == client_id)
    )
    if empresa_id:
        query = query.where(InvMovimientoTable.c.empresa_id == empresa_id)
    if producto_id:
        query = query.where(InvMovimientoDetalleTable.c.producto_id == producto_id)
    if almacen_id:
        query = query.where(
            (InvMovimientoTable.c.almacen_origen_id == almacen_id)
            | (InvMovimientoTable.c.almacen_destino_id == almacen_id)
        )
    if fecha_desde:
        query = query.where(InvMovimientoTable.c.fecha_movimiento >= fecha_desde)
    if fecha_hasta:
        query = query.where(InvMovimientoTable.c.fecha_movimiento <= fecha_hasta)
    query = query.order_by(InvMovimientoTable.c.fecha_movimiento.desc())
    return await execute_query(query, client_id=client_id)

