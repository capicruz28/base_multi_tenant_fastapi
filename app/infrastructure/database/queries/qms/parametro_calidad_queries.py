"""
Queries SQLAlchemy Core para qms_parametro_calidad.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import QmsParametroCalidadTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in QmsParametroCalidadTable.c}


async def list_parametros_calidad(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_parametro: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista parámetros de calidad del tenant."""
    query = select(QmsParametroCalidadTable).where(
        QmsParametroCalidadTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(QmsParametroCalidadTable.c.empresa_id == empresa_id)
    if tipo_parametro:
        query = query.where(QmsParametroCalidadTable.c.tipo_parametro == tipo_parametro)
    if solo_activos:
        query = query.where(QmsParametroCalidadTable.c.es_activo == True)
    if buscar:
        search_filter = or_(
            QmsParametroCalidadTable.c.nombre.ilike(f"%{buscar}%"),
            QmsParametroCalidadTable.c.codigo.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(QmsParametroCalidadTable.c.nombre)
    return await execute_query(query, client_id=client_id)


async def get_parametro_calidad_by_id(client_id: UUID, parametro_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un parámetro por id."""
    query = select(QmsParametroCalidadTable).where(
        and_(
            QmsParametroCalidadTable.c.cliente_id == client_id,
            QmsParametroCalidadTable.c.parametro_id == parametro_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_parametro_calidad(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un parámetro de calidad."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("parametro_id", uuid4())
    stmt = insert(QmsParametroCalidadTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_parametro_calidad_by_id(client_id, payload["parametro_id"])


async def update_parametro_calidad(
    client_id: UUID, parametro_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un parámetro de calidad."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("parametro_id", "cliente_id")
    }
    if not payload:
        return await get_parametro_calidad_by_id(client_id, parametro_id)
    stmt = (
        update(QmsParametroCalidadTable)
        .where(
            and_(
                QmsParametroCalidadTable.c.cliente_id == client_id,
                QmsParametroCalidadTable.c.parametro_id == parametro_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_parametro_calidad_by_id(client_id, parametro_id)
