"""
Queries SQLAlchemy Core para sls_pedido_detalle.
Detalle embebido en el pedido (no CRUD independiente).
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import delete, insert, text

from app.core.tenant.routing import get_connection_for_tenant
from app.infrastructure.database.tables_erp import SlsPedidoDetalleTable

_INSERTABLE_COLUMNS = {c.name for c in SlsPedidoDetalleTable.c}


async def list_detalle_by_pedido_id(
    client_id: UUID,
    pedido_id: UUID,
) -> List[Dict[str, Any]]:
    """
    Retorna detalle de un pedido con columnas calculadas de BD.
    Incluye: precio_neto, subtotal, igv, total, cantidad_pendiente (PERSISTED).
    """
    query = text(
        """
        SELECT
            pedido_detalle_id,
            cliente_id,
            empresa_id,
            pedido_id,
            producto_id,
            cantidad_pedida,
            unidad_medida_id,
            precio_unitario,
            descuento_porcentaje,
            precio_neto,
            subtotal,
            igv,
            total,
            cantidad_despachada,
            cantidad_pendiente,
            cantidad_facturada,
            almacen_origen_id,
            observaciones,
            fecha_creacion
        FROM sls_pedido_detalle
        WHERE cliente_id = :cliente_id
          AND pedido_id = :pedido_id
        ORDER BY fecha_creacion ASC
        """
    ).bindparams(cliente_id=client_id, pedido_id=pedido_id)

    async with get_connection_for_tenant(cliente_id=client_id) as session:
        result = await session.execute(query)
        rows = result.fetchall()
        cols = result.keys()
        return [dict(zip(cols, row)) for row in rows]


async def replace_detalle_pedido(
    client_id: UUID,
    empresa_id: UUID,
    pedido_id: UUID,
    items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Reemplaza el detalle completo de un pedido:
    - DELETE detalle existente (del tenant)
    - INSERT nuevos items
    Operación atómica con transacción.
    """
    now = datetime.utcnow()

    delete_stmt = delete(SlsPedidoDetalleTable).where(
        SlsPedidoDetalleTable.c.cliente_id == client_id,
        SlsPedidoDetalleTable.c.pedido_id == pedido_id,
    )

    payloads: List[Dict[str, Any]] = []
    for item in items:
        payload = {k: v for k, v in item.items() if k in _INSERTABLE_COLUMNS}
        payload["cliente_id"] = client_id
        payload["empresa_id"] = empresa_id
        payload["pedido_id"] = pedido_id
        payload.setdefault("fecha_creacion", now)
        payloads.append(payload)

    async with get_connection_for_tenant(cliente_id=client_id) as session:
        async with session.begin():
            await session.execute(delete_stmt)
            if payloads:
                await session.execute(insert(SlsPedidoDetalleTable), payloads)

    return await list_detalle_by_pedido_id(client_id=client_id, pedido_id=pedido_id)

