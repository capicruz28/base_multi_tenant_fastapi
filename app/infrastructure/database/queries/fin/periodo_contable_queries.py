"""
Queries SQLAlchemy Core para fin_periodo_contable.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_, func

from app.infrastructure.database.tables_erp import FinPeriodoContableTable, FinAsientoContableTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in FinPeriodoContableTable.c}


async def list_periodos_contables(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    año: Optional[int] = None,
    mes: Optional[int] = None,
    estado: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista periodos contables del tenant. Siempre filtra por cliente_id."""
    query = select(FinPeriodoContableTable).where(
        FinPeriodoContableTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(FinPeriodoContableTable.c.empresa_id == empresa_id)
    if año:
        query = query.where(FinPeriodoContableTable.c.año == año)
    if mes:
        query = query.where(FinPeriodoContableTable.c.mes == mes)
    if estado:
        query = query.where(FinPeriodoContableTable.c.estado == estado)
    query = query.order_by(FinPeriodoContableTable.c.año.desc(), FinPeriodoContableTable.c.mes.desc())
    return await execute_query(query, client_id=client_id)


async def get_periodo_contable_by_id(client_id: UUID, periodo_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un periodo contable por id. Exige cliente_id para no cruzar tenants."""
    query = select(FinPeriodoContableTable).where(
        and_(
            FinPeriodoContableTable.c.cliente_id == client_id,
            FinPeriodoContableTable.c.periodo_id == periodo_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_periodo_contable(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un periodo contable. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("periodo_id", uuid4())
    stmt = insert(FinPeriodoContableTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_periodo_contable_by_id(client_id, payload["periodo_id"])


async def update_periodo_contable(
    client_id: UUID, periodo_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un periodo contable. WHERE incluye cliente_id y periodo_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("periodo_id", "cliente_id")
    }
    if not payload:
        return await get_periodo_contable_by_id(client_id, periodo_id)
    stmt = (
        update(FinPeriodoContableTable)
        .where(
            and_(
                FinPeriodoContableTable.c.cliente_id == client_id,
                FinPeriodoContableTable.c.periodo_id == periodo_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_periodo_contable_by_id(client_id, periodo_id)


async def count_asientos_borrador_en_periodo(
    client_id: UUID,
    periodo_id: UUID,
) -> int:
    """Cantidad de asientos en estado borrador para el periodo."""
    q = (
        select(func.count())
        .select_from(FinAsientoContableTable)
        .where(
            and_(
                FinAsientoContableTable.c.cliente_id == client_id,
                FinAsientoContableTable.c.periodo_id == periodo_id,
                FinAsientoContableTable.c.estado == "borrador",
            )
        )
    )
    rows = await execute_query(q, client_id=client_id)
    if not rows:
        return 0
    return int(next(iter(rows[0].values())))


async def cerrar_periodo_contable(
    client_id: UUID,
    periodo_id: UUID,
    cerrado_por_usuario_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Marca el periodo como cerrado con auditoría de cierre."""
    stmt = (
        update(FinPeriodoContableTable)
        .where(
            and_(
                FinPeriodoContableTable.c.cliente_id == client_id,
                FinPeriodoContableTable.c.periodo_id == periodo_id,
            )
        )
        .values(
            estado="cerrado",
            fecha_cierre=datetime.utcnow(),
            cerrado_por_usuario_id=cerrado_por_usuario_id,
        )
    )
    await execute_update(stmt, client_id=client_id)
    return await get_periodo_contable_by_id(client_id, periodo_id)
