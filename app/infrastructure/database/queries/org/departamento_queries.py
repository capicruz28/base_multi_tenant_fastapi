"""
Queries SQLAlchemy Core para org_departamento.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import OrgDepartamentoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in OrgDepartamentoTable.c}


async def list_departamentos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
) -> List[Dict[str, Any]]:
    """Lista departamentos del tenant. Opcionalmente por empresa_id."""
    query = select(OrgDepartamentoTable).where(
        OrgDepartamentoTable.c.cliente_id == client_id
    )
    if empresa_id is not None:
        query = query.where(OrgDepartamentoTable.c.empresa_id == empresa_id)
    if solo_activos:
        query = query.where(OrgDepartamentoTable.c.es_activo == True)
    query = query.order_by(OrgDepartamentoTable.c.codigo)
    return await execute_query(query, client_id=client_id)


async def get_departamento_by_id(
    client_id: UUID, departamento_id: UUID
) -> Optional[Dict[str, Any]]:
    """Obtiene un departamento por id. Exige cliente_id."""
    query = select(OrgDepartamentoTable).where(
        and_(
            OrgDepartamentoTable.c.cliente_id == client_id,
            OrgDepartamentoTable.c.departamento_id == departamento_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_departamento(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un departamento. cliente_id se fuerza desde contexto."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("departamento_id", uuid4())
    stmt = insert(OrgDepartamentoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_departamento_by_id(client_id, payload["departamento_id"])


async def update_departamento(
    client_id: UUID, departamento_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un departamento. WHERE incluye cliente_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("departamento_id", "cliente_id")
    }
    if not payload:
        return await get_departamento_by_id(client_id, departamento_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(OrgDepartamentoTable)
        .where(
            and_(
                OrgDepartamentoTable.c.cliente_id == client_id,
                OrgDepartamentoTable.c.departamento_id == departamento_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_departamento_by_id(client_id, departamento_id)
