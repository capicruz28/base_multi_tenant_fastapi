"""
Queries SQLAlchemy Core para org_parametro_sistema.
Tenant: cliente_id. Híbrido Etapa C2: globales (empresa_id NULL) + overrides por empresa.
"""
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import OrgParametroSistemaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update
from app.core.tenant.empresa_context import coerce_empresa_id

_COLUMNS = {c.name for c in OrgParametroSistemaTable.c}


def _hybrid_read_filter(client_id: UUID, session_empresa_id: UUID):
    """Globales tenant + overrides de la empresa activa en sesión."""
    return and_(
        OrgParametroSistemaTable.c.cliente_id == client_id,
        or_(
            OrgParametroSistemaTable.c.empresa_id.is_(None),
            OrgParametroSistemaTable.c.empresa_id == session_empresa_id,
        ),
    )


def _parametro_exact_scope(
    client_id: UUID,
    parametro_id: UUID,
    row_empresa_id: Optional[UUID],
):
    """Ámbito exacto de la fila (global NULL o empresa concreta) para UPDATE/DELETE."""
    conds = [
        OrgParametroSistemaTable.c.cliente_id == client_id,
        OrgParametroSistemaTable.c.parametro_id == parametro_id,
    ]
    if row_empresa_id is None:
        conds.append(OrgParametroSistemaTable.c.empresa_id.is_(None))
    else:
        conds.append(OrgParametroSistemaTable.c.empresa_id == row_empresa_id)
    return and_(*conds)


def apply_parametro_precedence(
    rows: List[Dict[str, Any]],
    session_empresa_id: UUID,
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Precedencia: override empresa > global tenant por (modulo_codigo, codigo_parametro).

    Returns:
        (merged_rows, override_keys_count, global_only_count)
    """
    merged: Dict[Tuple[str, str], Dict[str, Any]] = {}
    override_keys = 0

    for row in rows:
        key = (row.get("modulo_codigo") or "", row.get("codigo_parametro") or "")
        row_empresa = coerce_empresa_id(row.get("empresa_id"))
        if row_empresa is not None and row_empresa == session_empresa_id:
            if key in merged and coerce_empresa_id(merged[key].get("empresa_id")) is None:
                override_keys += 1
            merged[key] = row
        elif row_empresa is None:
            merged.setdefault(key, row)

    result = list(merged.values())
    result.sort(key=lambda r: (r.get("modulo_codigo") or "", r.get("codigo_parametro") or ""))
    pure_global = sum(1 for r in result if coerce_empresa_id(r.get("empresa_id")) is None)
    return result, override_keys, pure_global


async def list_parametros_hybrid(
    client_id: UUID,
    session_empresa_id: UUID,
    modulo_codigo: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filas candidatas para lectura ERP híbrida (sin precedencia aplicada)."""
    query = select(OrgParametroSistemaTable).where(
        _hybrid_read_filter(client_id, session_empresa_id)
    )
    if modulo_codigo is not None:
        query = query.where(OrgParametroSistemaTable.c.modulo_codigo == modulo_codigo)
    if solo_activos:
        query = query.where(OrgParametroSistemaTable.c.es_activo == True)
    if buscar:
        query = query.where(
            or_(
                OrgParametroSistemaTable.c.modulo_codigo.ilike(f"%{buscar}%"),
                OrgParametroSistemaTable.c.codigo_parametro.ilike(f"%{buscar}%"),
                OrgParametroSistemaTable.c.nombre_parametro.ilike(f"%{buscar}%"),
            )
        )
    query = query.order_by(
        OrgParametroSistemaTable.c.modulo_codigo,
        OrgParametroSistemaTable.c.codigo_parametro,
    )
    return await execute_query(query, client_id=client_id)


async def get_parametro_by_id_raw(
    client_id: UUID,
    parametro_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Obtiene parámetro por id dentro del tenant (sin filtro empresa)."""
    query = select(OrgParametroSistemaTable).where(
        and_(
            OrgParametroSistemaTable.c.cliente_id == client_id,
            OrgParametroSistemaTable.c.parametro_id == parametro_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def get_parametro_by_clave_natural(
    client_id: UUID,
    modulo_codigo: str,
    codigo_parametro: str,
    empresa_id: Optional[UUID] = None,
    exclude_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """
    Lookup por UQ_parametro: (cliente_id, empresa_id, modulo_codigo, codigo_parametro).
    empresa_id None → fila global (empresa_id IS NULL).
    """
    conds = [
        OrgParametroSistemaTable.c.cliente_id == client_id,
        OrgParametroSistemaTable.c.modulo_codigo == modulo_codigo,
        OrgParametroSistemaTable.c.codigo_parametro == codigo_parametro,
    ]
    if empresa_id is None:
        conds.append(OrgParametroSistemaTable.c.empresa_id.is_(None))
    else:
        conds.append(OrgParametroSistemaTable.c.empresa_id == empresa_id)
    query = select(OrgParametroSistemaTable).where(and_(*conds))
    if exclude_id is not None:
        query = query.where(OrgParametroSistemaTable.c.parametro_id != exclude_id)
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_parametro(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un parámetro. cliente_id forzado; empresa_id según ámbito."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("parametro_id", uuid4())
    row_empresa_id = coerce_empresa_id(payload.get("empresa_id"))
    stmt = insert(OrgParametroSistemaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    row = await get_parametro_by_id_raw(client_id, payload["parametro_id"])
    return row


async def update_parametro(
    client_id: UUID,
    parametro_id: UUID,
    data: Dict[str, Any],
    row_empresa_id: Optional[UUID],
) -> Optional[Dict[str, Any]]:
    """Actualiza por ámbito exacto de la fila (global o empresa)."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS
        and k not in ("parametro_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_parametro_by_id_raw(client_id, parametro_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(OrgParametroSistemaTable)
        .where(_parametro_exact_scope(client_id, parametro_id, row_empresa_id))
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_parametro_by_id_raw(client_id, parametro_id)
