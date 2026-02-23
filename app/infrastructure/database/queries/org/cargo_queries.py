"""
Queries SQLAlchemy Core para org_cargo.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import OrgCargoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in OrgCargoTable.c}


async def list_cargos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
) -> List[Dict[str, Any]]:
    """Lista cargos del tenant. Opcionalmente por empresa_id."""
    query = select(OrgCargoTable).where(
        OrgCargoTable.c.cliente_id == client_id
    )
    if empresa_id is not None:
        query = query.where(OrgCargoTable.c.empresa_id == empresa_id)
    if solo_activos:
        query = query.where(OrgCargoTable.c.es_activo == True)
    query = query.order_by(OrgCargoTable.c.codigo)
    return await execute_query(query, client_id=client_id)


async def get_cargo_by_id(client_id: UUID, cargo_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un cargo por id. Exige cliente_id."""
    query = select(OrgCargoTable).where(
        and_(
            OrgCargoTable.c.cliente_id == client_id,
            OrgCargoTable.c.cargo_id == cargo_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_cargo(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un cargo. cliente_id se fuerza desde contexto."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("cargo_id", uuid4())
    stmt = insert(OrgCargoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_cargo_by_id(client_id, payload["cargo_id"])


async def update_cargo(
    client_id: UUID, cargo_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un cargo. WHERE incluye cliente_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("cargo_id", "cliente_id")
    }
    if not payload:
        return await get_cargo_by_id(client_id, cargo_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(OrgCargoTable)
        .where(
            and_(
                OrgCargoTable.c.cliente_id == client_id,
                OrgCargoTable.c.cargo_id == cargo_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_cargo_by_id(client_id, cargo_id)
