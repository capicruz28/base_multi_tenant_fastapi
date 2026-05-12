"""
Queries SQLAlchemy Core para pos_venta.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, case, func, or_

from app.infrastructure.database.tables_erp import PosVentaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PosVentaTable.c}
_SKIP_ON_WRITE = frozenset({"venta_id", "cliente_id", "total_cobrar", "monto_cambio"})


async def list_ventas(
    client_id: UUID,
    punto_venta_id: Optional[UUID] = None,
    turno_caja_id: Optional[UUID] = None,
    empresa_id: Optional[UUID] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Lista ventas POS del tenant."""
    query = select(PosVentaTable).where(
        PosVentaTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(PosVentaTable.c.empresa_id == empresa_id)
    if punto_venta_id:
        query = query.where(PosVentaTable.c.punto_venta_id == punto_venta_id)
    if turno_caja_id:
        query = query.where(PosVentaTable.c.turno_caja_id == turno_caja_id)
    if estado:
        query = query.where(PosVentaTable.c.estado == estado)
    if fecha_desde:
        query = query.where(PosVentaTable.c.fecha_venta >= fecha_desde)
    if fecha_hasta:
        query = query.where(PosVentaTable.c.fecha_venta <= fecha_hasta)
    query = query.order_by(PosVentaTable.c.fecha_venta.desc())
    return await execute_query(query, client_id=client_id)


async def get_venta_by_id(
    client_id: UUID,
    venta_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene una venta POS por id. Si empresa_id se informa, debe coincidir."""
    cond = [
        PosVentaTable.c.cliente_id == client_id,
        PosVentaTable.c.venta_id == venta_id,
    ]
    if empresa_id is not None:
        cond.append(PosVentaTable.c.empresa_id == empresa_id)
    query = select(PosVentaTable).where(and_(*cond))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_venta(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una venta POS."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS and k not in _SKIP_ON_WRITE}
    payload["cliente_id"] = client_id
    payload.setdefault("venta_id", uuid4())
    stmt = insert(PosVentaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_venta_by_id(client_id, payload["venta_id"])


async def update_venta(
    client_id: UUID,
    venta_id: UUID,
    data: Dict[str, Any],
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Actualiza una venta POS."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS and k not in _SKIP_ON_WRITE
    }
    if not payload:
        return await get_venta_by_id(client_id, venta_id, empresa_id=empresa_id)
    cond = [
        PosVentaTable.c.cliente_id == client_id,
        PosVentaTable.c.venta_id == venta_id,
    ]
    if empresa_id is not None:
        cond.append(PosVentaTable.c.empresa_id == empresa_id)
    stmt = update(PosVentaTable).where(and_(*cond)).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_venta_by_id(client_id, venta_id, empresa_id=empresa_id)


async def summarize_ventas_por_turno(
    client_id: UUID,
    turno_id: UUID,
) -> Dict[str, Any]:
    """
    Agrega ventas POS del turno (excluye anuladas) para cierre de caja:
    conteos y sumas por forma de pago y totales de comprobantes por tipo (heurística SUNAT-like).
    """
    base = and_(
        PosVentaTable.c.cliente_id == client_id,
        PosVentaTable.c.turno_caja_id == turno_id,
        PosVentaTable.c.estado != "anulada",
    )
    stmt = select(
        func.count().label("n_ventas"),
        func.coalesce(func.sum(PosVentaTable.c.monto_efectivo), 0).label("sum_efectivo"),
        func.coalesce(func.sum(PosVentaTable.c.monto_tarjeta), 0).label("sum_tarjeta"),
        func.coalesce(func.sum(PosVentaTable.c.monto_transferencia), 0).label(
            "sum_transferencia"
        ),
        func.coalesce(func.sum(PosVentaTable.c.monto_otros), 0).label("sum_otros"),
        func.coalesce(
            func.sum(
                case(
                    (
                        or_(
                            PosVentaTable.c.tipo_comprobante == "01",
                            PosVentaTable.c.tipo_comprobante == "F",
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("n_facturas"),
        func.coalesce(
            func.sum(
                case(
                    (
                        or_(
                            PosVentaTable.c.tipo_comprobante == "03",
                            PosVentaTable.c.tipo_comprobante == "B",
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("n_boletas"),
        func.coalesce(
            func.sum(
                case(
                    (
                        or_(
                            PosVentaTable.c.tipo_comprobante == "07",
                            PosVentaTable.c.tipo_comprobante == "NC",
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("n_notas_credito"),
    ).where(base)
    rows = await execute_query(stmt, client_id=client_id)
    return dict(rows[0]) if rows else {}


async def set_venta_anulada(
    client_id: UUID,
    venta_id: UUID,
    motivo_anulacion: str,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Marca la venta como anulada usando fecha de servidor en BD."""
    cond = [
        PosVentaTable.c.cliente_id == client_id,
        PosVentaTable.c.venta_id == venta_id,
    ]
    if empresa_id is not None:
        cond.append(PosVentaTable.c.empresa_id == empresa_id)
    stmt = (
        update(PosVentaTable)
        .where(and_(*cond))
        .values(
            estado="anulada",
            motivo_anulacion=motivo_anulacion,
            fecha_anulacion=func.getdate(),
        )
    )
    await execute_update(stmt, client_id=client_id)
    return await get_venta_by_id(client_id, venta_id, empresa_id=empresa_id)
