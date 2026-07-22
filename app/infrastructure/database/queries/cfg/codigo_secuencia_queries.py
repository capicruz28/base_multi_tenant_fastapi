"""Queries sobre cfg_codigo_secuencia (Etapa 5A lectura + 5B escritura).

Spec: cfg-implementation-spec v1.0 — G-04 / G-06.
Escrituras: exigen ``session`` UoW; no abren ni hacen begin/commit.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.tables import CfgCodigoSecuenciaTable

t = CfgCodigoSecuenciaTable

# Campos mutables vía update_codigo_secuencia_config (formato + generation_policy).
_CONFIG_UPDATE_FIELDS = frozenset(
    {
        "prefijo",
        "separador",
        "longitud_numero",
        "numero_inicial",
        "generation_policy",
    }
)


def _require_write_session(session: Optional[AsyncSession], operation: str) -> AsyncSession:
    if session is None:
        raise ValueError(
            f"Escritura cfg_codigo_secuencia requiere session UoW explícita ({operation})."
        )
    return session


def _row_to_dict(row) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    if hasattr(row, "_mapping"):
        mapping = row._mapping
        if mapping is not None:
            return dict(mapping)
    if isinstance(row, dict):
        return row
    return dict(row)


def _build_list_conditions(
    cliente_id: UUID,
    *,
    empresa_id: Optional[UUID] = None,
    scope_type: Optional[str] = None,
    sequence_key: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> list:
    conditions = [t.c.cliente_id == cliente_id]
    if empresa_id is not None:
        conditions.append(t.c.empresa_id == empresa_id)
    if scope_type is not None:
        conditions.append(t.c.scope_type == scope_type)
    if sequence_key is not None:
        conditions.append(t.c.sequence_key == sequence_key)
    if es_activo is not None:
        conditions.append(t.c.es_activo == es_activo)
    if buscar:
        pattern = f"%{buscar}%"
        conditions.append(
            or_(
                t.c.sequence_key.ilike(pattern),
                t.c.prefijo.ilike(pattern),
            )
        )
    return conditions


async def list_codigo_secuencias(
    cliente_id: UUID,
    *,
    empresa_id: Optional[UUID] = None,
    scope_type: Optional[str] = None,
    sequence_key: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
    session: Optional[AsyncSession] = None,
) -> List[Dict[str, Any]]:
    """Lista filas cfg del tenant con filtros nativos. Sin page/limit SQL (G-04)."""
    conditions = _build_list_conditions(
        cliente_id,
        empresa_id=empresa_id,
        scope_type=scope_type,
        sequence_key=sequence_key,
        es_activo=es_activo,
        buscar=buscar,
    )
    # ORDER BY estable de fetch; sort API / page se aplican en el service.
    query = (
        select(t)
        .where(and_(*conditions))
        .order_by(t.c.sequence_key.asc(), t.c.secuencia_id.asc())
    )
    if session is not None:
        result = await session.execute(query)
        return [_row_to_dict(row) for row in result.fetchall()]
    return await execute_query(query, client_id=cliente_id)


async def get_codigo_secuencia_by_id(
    cliente_id: UUID,
    secuencia_id: UUID,
    *,
    session: Optional[AsyncSession] = None,
) -> Optional[Dict[str, Any]]:
    """Obtiene una secuencia por id dentro del tenant. Cross-tenant → None."""
    query = select(t).where(
        and_(
            t.c.secuencia_id == secuencia_id,
            t.c.cliente_id == cliente_id,
        )
    )
    if session is not None:
        result = await session.execute(query)
        return _row_to_dict(result.fetchone())
    rows = await execute_query(query, client_id=cliente_id)
    return rows[0] if rows else None


async def update_codigo_secuencia_config(
    cliente_id: UUID,
    secuencia_id: UUID,
    data: Dict[str, Any],
    *,
    session: AsyncSession,
    usuario_actualizacion_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza campos de formato + generation_policy + auditoría. No toca contador/scope.

    ``session`` obligatoria (UoW del service). No hace begin/commit.
    """
    session = _require_write_session(session, "update_codigo_secuencia_config")
    payload = {k: v for k, v in data.items() if k in _CONFIG_UPDATE_FIELDS}
    if not payload:
        return await get_codigo_secuencia_by_id(
            cliente_id, secuencia_id, session=session
        )
    payload["fecha_actualizacion"] = datetime.utcnow()
    payload["usuario_actualizacion_id"] = usuario_actualizacion_id
    stmt = (
        update(t)
        .where(
            and_(
                t.c.secuencia_id == secuencia_id,
                t.c.cliente_id == cliente_id,
            )
        )
        .values(**payload)
    )
    await session.execute(stmt)
    return await get_codigo_secuencia_by_id(
        cliente_id, secuencia_id, session=session
    )


async def set_codigo_secuencia_activo(
    cliente_id: UUID,
    secuencia_id: UUID,
    es_activo: bool,
    *,
    session: AsyncSession,
    usuario_actualizacion_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Actualiza solo es_activo + auditoría. No hace begin/commit."""
    session = _require_write_session(session, "set_codigo_secuencia_activo")
    stmt = (
        update(t)
        .where(
            and_(
                t.c.secuencia_id == secuencia_id,
                t.c.cliente_id == cliente_id,
            )
        )
        .values(
            es_activo=es_activo,
            fecha_actualizacion=datetime.utcnow(),
            usuario_actualizacion_id=usuario_actualizacion_id,
        )
    )
    await session.execute(stmt)
    return await get_codigo_secuencia_by_id(
        cliente_id, secuencia_id, session=session
    )
