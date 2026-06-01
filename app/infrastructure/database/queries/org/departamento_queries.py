"""
Queries SQLAlchemy Core para org_departamento.
Filtro tenant: cliente_id. Aislamiento empresa: empresa_id obligatorio (Etapa B).
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import OrgDepartamentoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions

_COLUMNS = {c.name for c in OrgDepartamentoTable.c}


async def list_departamentos(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
) -> List[Dict[str, Any]]:
    """Lista departamentos del tenant y empresa activa."""
    query = select(OrgDepartamentoTable).where(
        and_(
            OrgDepartamentoTable.c.cliente_id == client_id,
            OrgDepartamentoTable.c.empresa_id == empresa_id,
        )
    )
    if solo_activos:
        query = query.where(OrgDepartamentoTable.c.es_activo == True)
    query = query.order_by(OrgDepartamentoTable.c.codigo)
    return await execute_query(query, client_id=client_id)


async def get_departamento_by_id(
    client_id: UUID,
    departamento_id: UUID,
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Obtiene un departamento por id. Triple filtro cliente + empresa + departamento."""
    query = select(OrgDepartamentoTable).where(
        empresa_scoped_conditions(
            OrgDepartamentoTable,
            client_id=client_id,
            empresa_id=empresa_id,
            entity_id_column=OrgDepartamentoTable.c.departamento_id,
            entity_id=departamento_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def get_departamento_by_codigo(
    client_id: UUID,
    empresa_id: UUID,
    codigo: str,
    exclude_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Lookup por codigo dentro del tenant+empresa."""
    query = select(OrgDepartamentoTable).where(
        and_(
            OrgDepartamentoTable.c.cliente_id == client_id,
            OrgDepartamentoTable.c.empresa_id == empresa_id,
            OrgDepartamentoTable.c.codigo == codigo,
        )
    )
    if exclude_id is not None:
        query = query.where(OrgDepartamentoTable.c.departamento_id != exclude_id)
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_departamento(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un departamento. cliente_id y empresa_id desde contexto."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("departamento_id", uuid4())
    empresa_id = payload["empresa_id"]
    stmt = insert(OrgDepartamentoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_departamento_by_id(
        client_id, payload["departamento_id"], empresa_id=empresa_id
    )


async def update_departamento(
    client_id: UUID,
    departamento_id: UUID,
    data: Dict[str, Any],
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza un departamento. WHERE: cliente_id + empresa_id + departamento_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS
        and k not in ("departamento_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_departamento_by_id(client_id, departamento_id, empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(OrgDepartamentoTable)
        .where(
            empresa_scoped_conditions(
                OrgDepartamentoTable,
                client_id=client_id,
                empresa_id=empresa_id,
                entity_id_column=OrgDepartamentoTable.c.departamento_id,
                entity_id=departamento_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_departamento_by_id(client_id, departamento_id, empresa_id)
