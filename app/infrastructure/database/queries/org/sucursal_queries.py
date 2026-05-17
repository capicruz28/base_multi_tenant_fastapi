"""
Queries SQLAlchemy Core para org_sucursal.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import OrgSucursalTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in OrgSucursalTable.c}


async def list_sucursales(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
) -> List[Dict[str, Any]]:
    """Lista sucursales del tenant. Opcionalmente por empresa_id."""
    query = select(OrgSucursalTable).where(
        OrgSucursalTable.c.cliente_id == client_id
    )
    if empresa_id is not None:
        query = query.where(OrgSucursalTable.c.empresa_id == empresa_id)
    if solo_activos:
        query = query.where(OrgSucursalTable.c.es_activo == True)
    query = query.order_by(OrgSucursalTable.c.codigo)
    return await execute_query(query, client_id=client_id)


async def get_sucursal_by_codigo(
    client_id: UUID,
    empresa_id: UUID,
    codigo: str,
    exclude_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Lookup por codigo dentro del tenant+empresa. exclude_id omite el propio registro en UPDATE."""
    query = select(OrgSucursalTable).where(
        and_(
            OrgSucursalTable.c.cliente_id == client_id,
            OrgSucursalTable.c.empresa_id == empresa_id,
            OrgSucursalTable.c.codigo == codigo,
        )
    )
    if exclude_id is not None:
        query = query.where(OrgSucursalTable.c.sucursal_id != exclude_id)
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


def _sucursal_id_conditions(
    client_id: UUID, sucursal_id: UUID, empresa_id: Optional[UUID]
):
    conds = [
        OrgSucursalTable.c.cliente_id == client_id,
        OrgSucursalTable.c.sucursal_id == sucursal_id,
    ]
    if empresa_id is not None:
        conds.append(OrgSucursalTable.c.empresa_id == empresa_id)
    return and_(*conds)


async def get_sucursal_by_id(
    client_id: UUID,
    sucursal_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene una sucursal por id. Exige cliente_id; opcionalmente restringe por empresa_id."""
    query = select(OrgSucursalTable).where(
        _sucursal_id_conditions(client_id, sucursal_id, empresa_id)
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_sucursal(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una sucursal. cliente_id se fuerza desde contexto."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("sucursal_id", uuid4())
    stmt = insert(OrgSucursalTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_sucursal_by_id(client_id, payload["sucursal_id"], None)


async def update_sucursal(
    client_id: UUID,
    sucursal_id: UUID,
    data: Dict[str, Any],
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Actualiza una sucursal. WHERE incluye cliente_id y opcionalmente empresa_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("sucursal_id", "cliente_id")
    }
    if not payload:
        return await get_sucursal_by_id(client_id, sucursal_id, empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(OrgSucursalTable)
        .where(_sucursal_id_conditions(client_id, sucursal_id, empresa_id))
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_sucursal_by_id(client_id, sucursal_id, empresa_id)
