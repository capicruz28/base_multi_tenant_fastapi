"""
Queries SQLAlchemy Core para org_empresa.
Filtro tenant estricto: cliente_id obligatorio en todas las operaciones (Etapa C1).
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import OrgEmpresaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.company_scope import tenant_empresa_scoped_conditions
from app.shared.pagination.query_helpers import apply_erp_sort

_COLUMNS = {c.name for c in OrgEmpresaTable.c}

_SORT_COLUMNS_EMPRESA = frozenset(
    {"codigo_empresa", "razon_social", "nombre_comercial", "ruc", "fecha_creacion"}
)
_SORT_COLUMN_MAP = {
    "codigo_empresa": OrgEmpresaTable.c.codigo_empresa,
    "razon_social": OrgEmpresaTable.c.razon_social,
    "nombre_comercial": OrgEmpresaTable.c.nombre_comercial,
    "ruc": OrgEmpresaTable.c.ruc,
    "fecha_creacion": OrgEmpresaTable.c.fecha_creacion,
}
_DEFAULT_EMPRESA_ORDER = [(OrgEmpresaTable.c.razon_social, "asc")]


def _build_empresa_list_conditions(
    client_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> list:
    conditions = [OrgEmpresaTable.c.cliente_id == client_id]
    if solo_activos:
        conditions.append(OrgEmpresaTable.c.es_activo == True)
    if buscar:
        conditions.append(
            or_(
                OrgEmpresaTable.c.codigo_empresa.ilike(f"%{buscar}%"),
                OrgEmpresaTable.c.razon_social.ilike(f"%{buscar}%"),
                OrgEmpresaTable.c.nombre_comercial.ilike(f"%{buscar}%"),
            )
        )
    return conditions


async def list_empresas(
    client_id: UUID,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista empresas del tenant. Siempre filtra por cliente_id."""
    conditions = _build_empresa_list_conditions(client_id, solo_activos, buscar)
    query = select(OrgEmpresaTable).where(and_(*conditions))
    query = apply_erp_sort(
        query,
        allowed_columns=_SORT_COLUMNS_EMPRESA,
        column_map=_SORT_COLUMN_MAP,
        sort_by=sort_by,
        sort_dir=sort_dir,
        default_order=_DEFAULT_EMPRESA_ORDER,
        tie_breaker=("empresa_id", OrgEmpresaTable.c.empresa_id),
    )
    return await execute_query(query, client_id=client_id)


async def get_empresa_by_codigo(
    client_id: UUID,
    codigo_empresa: str,
    exclude_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Lookup por codigo_empresa dentro del tenant."""
    query = select(OrgEmpresaTable).where(
        and_(
            OrgEmpresaTable.c.cliente_id == client_id,
            OrgEmpresaTable.c.codigo_empresa == codigo_empresa,
        )
    )
    if exclude_id is not None:
        query = query.where(OrgEmpresaTable.c.empresa_id != exclude_id)
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def get_empresa_by_ruc(
    client_id: UUID,
    ruc: str,
    exclude_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Lookup por RUC dentro del tenant."""
    query = select(OrgEmpresaTable).where(
        and_(
            OrgEmpresaTable.c.cliente_id == client_id,
            OrgEmpresaTable.c.ruc == ruc,
        )
    )
    if exclude_id is not None:
        query = query.where(OrgEmpresaTable.c.empresa_id != exclude_id)
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def get_empresa_by_id(client_id: UUID, empresa_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una empresa. Triple filtro implícito: cliente_id + empresa_id."""
    query = select(OrgEmpresaTable).where(
        tenant_empresa_scoped_conditions(
            OrgEmpresaTable,
            client_id=client_id,
            empresa_id=empresa_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_empresa(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una empresa. cliente_id se fuerza desde contexto de sesión."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("empresa_id", uuid4())
    empresa_id = payload["empresa_id"]
    stmt = insert(OrgEmpresaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_empresa_by_id(client_id, empresa_id)


async def update_empresa(
    client_id: UUID,
    empresa_id: UUID,
    data: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Actualiza una empresa. WHERE: cliente_id + empresa_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS and k not in ("empresa_id", "cliente_id")
    }
    if not payload:
        return await get_empresa_by_id(client_id, empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(OrgEmpresaTable)
        .where(
            tenant_empresa_scoped_conditions(
                OrgEmpresaTable,
                client_id=client_id,
                empresa_id=empresa_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_empresa_by_id(client_id, empresa_id)
