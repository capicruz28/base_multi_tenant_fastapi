"""
Queries SQLAlchemy Core para org_sucursal.
Filtro tenant: cliente_id. Aislamiento empresa: empresa_id obligatorio (Etapa B).
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import OrgSucursalTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import empresa_scoped_conditions
from app.shared.pagination.query_helpers import apply_erp_sort

_COLUMNS = {c.name for c in OrgSucursalTable.c}

_SORT_COLUMNS_SUCURSAL = frozenset({"codigo", "nombre", "tipo_sucursal", "fecha_creacion"})
_SORT_COLUMN_MAP = {
    "codigo": OrgSucursalTable.c.codigo,
    "nombre": OrgSucursalTable.c.nombre,
    "tipo_sucursal": OrgSucursalTable.c.tipo_sucursal,
    "fecha_creacion": OrgSucursalTable.c.fecha_creacion,
}
_DEFAULT_SUCURSAL_ORDER = [(OrgSucursalTable.c.codigo, "asc")]


def _build_sucursal_list_conditions(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> list:
    conditions = [
        OrgSucursalTable.c.cliente_id == client_id,
        OrgSucursalTable.c.empresa_id == empresa_id,
    ]
    if solo_activos:
        conditions.append(OrgSucursalTable.c.es_activo == True)
    if buscar:
        conditions.append(
            or_(
                OrgSucursalTable.c.codigo.ilike(f"%{buscar}%"),
                OrgSucursalTable.c.nombre.ilike(f"%{buscar}%"),
            )
        )
    return conditions


async def list_sucursales(
    client_id: UUID,
    empresa_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista sucursales del tenant y empresa activa."""
    conditions = _build_sucursal_list_conditions(
        client_id, empresa_id, solo_activos, buscar
    )
    query = select(OrgSucursalTable).where(and_(*conditions))
    query = apply_erp_sort(
        query,
        allowed_columns=_SORT_COLUMNS_SUCURSAL,
        column_map=_SORT_COLUMN_MAP,
        sort_by=sort_by,
        sort_dir=sort_dir,
        default_order=_DEFAULT_SUCURSAL_ORDER,
        tie_breaker=("sucursal_id", OrgSucursalTable.c.sucursal_id),
    )
    return await execute_query(query, client_id=client_id)


async def get_sucursal_by_codigo(
    client_id: UUID,
    empresa_id: UUID,
    codigo: str,
    exclude_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Lookup por codigo dentro del tenant+empresa."""
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


async def get_sucursal_by_id(
    client_id: UUID,
    sucursal_id: UUID,
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Obtiene una sucursal por id. Triple filtro cliente + empresa + sucursal."""
    query = select(OrgSucursalTable).where(
        empresa_scoped_conditions(
            OrgSucursalTable,
            client_id=client_id,
            empresa_id=empresa_id,
            entity_id_column=OrgSucursalTable.c.sucursal_id,
            entity_id=sucursal_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_sucursal(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una sucursal. cliente_id y empresa_id se fuerzan desde contexto."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("sucursal_id", uuid4())
    empresa_id = payload["empresa_id"]
    stmt = insert(OrgSucursalTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_sucursal_by_id(
        client_id, payload["sucursal_id"], empresa_id=empresa_id
    )


async def update_sucursal(
    client_id: UUID,
    sucursal_id: UUID,
    data: Dict[str, Any],
    empresa_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza una sucursal. WHERE: cliente_id + empresa_id + sucursal_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS and k not in ("sucursal_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_sucursal_by_id(client_id, sucursal_id, empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(OrgSucursalTable)
        .where(
            empresa_scoped_conditions(
                OrgSucursalTable,
                client_id=client_id,
                empresa_id=empresa_id,
                entity_id_column=OrgSucursalTable.c.sucursal_id,
                entity_id=sucursal_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_sucursal_by_id(client_id, sucursal_id, empresa_id)
