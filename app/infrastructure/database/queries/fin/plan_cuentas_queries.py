"""
Queries SQLAlchemy Core para fin_plan_cuentas.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import FinPlanCuentasTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in FinPlanCuentasTable.c}


async def list_plan_cuentas(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    cuenta_padre_id: Optional[UUID] = None,
    tipo_cuenta: Optional[str] = None,
    nivel: Optional[int] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista cuentas del plan contable del tenant. Siempre filtra por cliente_id."""
    query = select(FinPlanCuentasTable).where(
        FinPlanCuentasTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(FinPlanCuentasTable.c.empresa_id == empresa_id)
    if cuenta_padre_id:
        query = query.where(FinPlanCuentasTable.c.cuenta_padre_id == cuenta_padre_id)
    if tipo_cuenta:
        query = query.where(FinPlanCuentasTable.c.tipo_cuenta == tipo_cuenta)
    if nivel is not None:
        query = query.where(FinPlanCuentasTable.c.nivel == nivel)
    if solo_activos:
        query = query.where(FinPlanCuentasTable.c.es_activo == True)
    if buscar:
        search_filter = or_(
            FinPlanCuentasTable.c.nombre_cuenta.ilike(f"%{buscar}%"),
            FinPlanCuentasTable.c.codigo_cuenta.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(FinPlanCuentasTable.c.codigo_cuenta)
    return await execute_query(query, client_id=client_id)


async def get_cuenta_by_id(client_id: UUID, cuenta_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una cuenta por id. Exige cliente_id para no cruzar tenants."""
    query = select(FinPlanCuentasTable).where(
        and_(
            FinPlanCuentasTable.c.cliente_id == client_id,
            FinPlanCuentasTable.c.cuenta_id == cuenta_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_cuenta(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una cuenta. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("cuenta_id", uuid4())
    stmt = insert(FinPlanCuentasTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_cuenta_by_id(client_id, payload["cuenta_id"])


async def update_cuenta(
    client_id: UUID, cuenta_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una cuenta. WHERE incluye cliente_id y cuenta_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("cuenta_id", "cliente_id")
    }
    if not payload:
        return await get_cuenta_by_id(client_id, cuenta_id)
    stmt = (
        update(FinPlanCuentasTable)
        .where(
            and_(
                FinPlanCuentasTable.c.cliente_id == client_id,
                FinPlanCuentasTable.c.cuenta_id == cuenta_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_cuenta_by_id(client_id, cuenta_id)
