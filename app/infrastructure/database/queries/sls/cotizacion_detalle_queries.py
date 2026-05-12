"""
Queries SQLAlchemy Core para sls_cotizacion_detalle.
Detalle embebido en la cotización (no CRUD independiente).
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import delete, insert, text

from app.core.tenant.routing import get_connection_for_tenant
from app.infrastructure.database.tables_erp import SlsCotizacionDetalleTable

_INSERTABLE_COLUMNS = {c.name for c in SlsCotizacionDetalleTable.c}


async def list_detalle_by_cotizacion_id(
    client_id: UUID,
    cotizacion_id: UUID,
) -> List[Dict[str, Any]]:
    """
    Retorna detalle de una cotización con columnas calculadas de BD.
    Incluye: precio_neto, subtotal, igv, total (PERSISTED en SQL).
    """
    # Usar TextClause para poder seleccionar columnas calculadas que no están en SQLAlchemy Table.
    query = text(
        """
        SELECT
            cotizacion_detalle_id,
            cliente_id,
            empresa_id,
            cotizacion_id,
            producto_id,
            cantidad,
            unidad_medida_id,
            precio_unitario,
            descuento_porcentaje,
            precio_neto,
            subtotal,
            igv,
            total,
            tiempo_entrega_dias,
            observaciones,
            fecha_creacion
        FROM sls_cotizacion_detalle
        WHERE cliente_id = :cliente_id
          AND cotizacion_id = :cotizacion_id
        ORDER BY fecha_creacion ASC
        """
    ).bindparams(cliente_id=client_id, cotizacion_id=cotizacion_id)

    async with get_connection_for_tenant(cliente_id=client_id) as session:
        result = await session.execute(query)
        rows = result.fetchall()
        cols = result.keys()
        return [dict(zip(cols, row)) for row in rows]


async def replace_detalle_cotizacion(
    client_id: UUID,
    empresa_id: UUID,
    cotizacion_id: UUID,
    items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Reemplaza el detalle completo de una cotización:
    - DELETE detalle existente (del tenant)
    - INSERT nuevos items
    Operación atómica con transacción.
    """
    now = datetime.utcnow()

    delete_stmt = delete(SlsCotizacionDetalleTable).where(
        SlsCotizacionDetalleTable.c.cliente_id == client_id,
        SlsCotizacionDetalleTable.c.cotizacion_id == cotizacion_id,
    )

    # Normalizar payload (solo columnas insertables, forzar tenant/empresa/cotizacion)
    payloads: List[Dict[str, Any]] = []
    for item in items:
        payload = {k: v for k, v in item.items() if k in _INSERTABLE_COLUMNS}
        payload["cliente_id"] = client_id
        payload["empresa_id"] = empresa_id
        payload["cotizacion_id"] = cotizacion_id
        payload.setdefault("fecha_creacion", now)
        payloads.append(payload)

    async with get_connection_for_tenant(cliente_id=client_id) as session:
        async with session.begin():
            await session.execute(delete_stmt)
            if payloads:
                await session.execute(insert(SlsCotizacionDetalleTable), payloads)

    return await list_detalle_by_cotizacion_id(client_id=client_id, cotizacion_id=cotizacion_id)

