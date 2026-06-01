"""
Queries SQLAlchemy Core para org_centro_costo.
Filtro tenant: cliente_id. Aislamiento empresa: empresa_id obligatorio (Etapa B).
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_

from app.infrastructure.database.tables_erp import OrgCentroCostoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions

_COLUMNS = {c.name for c in OrgCentroCostoTable.c}


async def list_centros_costo(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
) -> List[Dict[str, Any]]:
    """Lista centros de costo del tenant y empresa activa."""
    query = select(OrgCentroCostoTable).where(
        and_(
            OrgCentroCostoTable.c.cliente_id == client_id,
            OrgCentroCostoTable.c.empresa_id == empresa_id,
        )
    )
    if solo_activos:
        query = query.where(OrgCentroCostoTable.c.es_activo == True)
    query = query.order_by(OrgCentroCostoTable.c.codigo)
    return await execute_query(query, client_id=client_id)


async def get_centro_costo_by_id(
    client_id: UUID,
    centro_costo_id: UUID,
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Obtiene un centro de costo por id. Triple filtro."""
    query = select(OrgCentroCostoTable).where(
        empresa_scoped_conditions(
            OrgCentroCostoTable,
            client_id=client_id,
            empresa_id=empresa_id,
            entity_id_column=OrgCentroCostoTable.c.centro_costo_id,
            entity_id=centro_costo_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def get_centro_costo_by_codigo(
    client_id: UUID,
    empresa_id: UUID,
    codigo: str,
    exclude_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Lookup por codigo dentro del tenant+empresa."""
    query = select(OrgCentroCostoTable).where(
        and_(
            OrgCentroCostoTable.c.cliente_id == client_id,
            OrgCentroCostoTable.c.empresa_id == empresa_id,
            OrgCentroCostoTable.c.codigo == codigo,
        )
    )
    if exclude_id is not None:
        query = query.where(OrgCentroCostoTable.c.centro_costo_id != exclude_id)
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_centro_costo(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un centro de costo. cliente_id y empresa_id desde contexto."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("centro_costo_id", uuid4())
    empresa_id = payload["empresa_id"]
    stmt = insert(OrgCentroCostoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_centro_costo_by_id(
        client_id, payload["centro_costo_id"], empresa_id=empresa_id
    )


async def update_centro_costo(
    client_id: UUID,
    centro_costo_id: UUID,
    data: Dict[str, Any],
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza un centro de costo. WHERE: cliente_id + empresa_id + centro_costo_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS
        and k not in ("centro_costo_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_centro_costo_by_id(client_id, centro_costo_id, empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(OrgCentroCostoTable)
        .where(
            empresa_scoped_conditions(
                OrgCentroCostoTable,
                client_id=client_id,
                empresa_id=empresa_id,
                entity_id_column=OrgCentroCostoTable.c.centro_costo_id,
                entity_id=centro_costo_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_centro_costo_by_id(client_id, centro_costo_id, empresa_id)
