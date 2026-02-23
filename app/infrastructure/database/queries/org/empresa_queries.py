"""
Queries SQLAlchemy Core para org_empresa.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import OrgEmpresaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in OrgEmpresaTable.c}


async def list_empresas(client_id: UUID, solo_activos: bool = True) -> List[Dict[str, Any]]:
    """Lista empresas del tenant. Siempre filtra por cliente_id."""
    query = select(OrgEmpresaTable).where(
        OrgEmpresaTable.c.cliente_id == client_id
    )
    if solo_activos:
        query = query.where(OrgEmpresaTable.c.es_activo == True)
    query = query.order_by(OrgEmpresaTable.c.razon_social)
    return await execute_query(query, client_id=client_id)


async def get_empresa_by_id(client_id: UUID, empresa_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una empresa por id. Exige cliente_id para no cruzar tenants."""
    query = select(OrgEmpresaTable).where(
        and_(
            OrgEmpresaTable.c.cliente_id == client_id,
            OrgEmpresaTable.c.empresa_id == empresa_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_empresa(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una empresa. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("empresa_id", uuid4())
    stmt = insert(OrgEmpresaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_empresa_by_id(client_id, payload["empresa_id"])


async def update_empresa(
    client_id: UUID, empresa_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una empresa. WHERE incluye cliente_id y empresa_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("empresa_id", "cliente_id")
    }
    if not payload:
        return await get_empresa_by_id(client_id, empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(OrgEmpresaTable)
        .where(
            and_(
                OrgEmpresaTable.c.cliente_id == client_id,
                OrgEmpresaTable.c.empresa_id == empresa_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_empresa_by_id(client_id, empresa_id)
