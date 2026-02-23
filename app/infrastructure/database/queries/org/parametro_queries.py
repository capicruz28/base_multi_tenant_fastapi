"""
Queries SQLAlchemy Core para org_parametro_sistema.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import OrgParametroSistemaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in OrgParametroSistemaTable.c}


async def list_parametros(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    modulo_codigo: Optional[str] = None,
    solo_activos: bool = True,
) -> List[Dict[str, Any]]:
    """Lista parámetros del tenant. Opcionalmente por empresa_id y modulo_codigo."""
    query = select(OrgParametroSistemaTable).where(
        OrgParametroSistemaTable.c.cliente_id == client_id
    )
    if empresa_id is not None:
        query = query.where(OrgParametroSistemaTable.c.empresa_id == empresa_id)
    if modulo_codigo is not None:
        query = query.where(
            OrgParametroSistemaTable.c.modulo_codigo == modulo_codigo
        )
    if solo_activos:
        query = query.where(OrgParametroSistemaTable.c.es_activo == True)
    query = query.order_by(
        OrgParametroSistemaTable.c.modulo_codigo,
        OrgParametroSistemaTable.c.codigo_parametro,
    )
    return await execute_query(query, client_id=client_id)


async def get_parametro_by_id(
    client_id: UUID, parametro_id: UUID
) -> Optional[Dict[str, Any]]:
    """Obtiene un parámetro por id. Exige cliente_id."""
    query = select(OrgParametroSistemaTable).where(
        and_(
            OrgParametroSistemaTable.c.cliente_id == client_id,
            OrgParametroSistemaTable.c.parametro_id == parametro_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_parametro(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un parámetro. cliente_id se fuerza desde contexto."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("parametro_id", uuid4())
    stmt = insert(OrgParametroSistemaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_parametro_by_id(client_id, payload["parametro_id"])


async def update_parametro(
    client_id: UUID, parametro_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un parámetro. WHERE incluye cliente_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("parametro_id", "cliente_id")
    }
    if not payload:
        return await get_parametro_by_id(client_id, parametro_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(OrgParametroSistemaTable)
        .where(
            and_(
                OrgParametroSistemaTable.c.cliente_id == client_id,
                OrgParametroSistemaTable.c.parametro_id == parametro_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_parametro_by_id(client_id, parametro_id)
