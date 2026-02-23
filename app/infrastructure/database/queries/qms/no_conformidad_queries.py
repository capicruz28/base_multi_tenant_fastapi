"""
Queries SQLAlchemy Core para qms_no_conformidad.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import QmsNoConformidadTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in QmsNoConformidadTable.c}


async def list_no_conformidades(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    origen: Optional[str] = None,
    tipo_nc: Optional[str] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista no conformidades del tenant."""
    query = select(QmsNoConformidadTable).where(
        QmsNoConformidadTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(QmsNoConformidadTable.c.empresa_id == empresa_id)
    if producto_id:
        query = query.where(QmsNoConformidadTable.c.producto_id == producto_id)
    if origen:
        query = query.where(QmsNoConformidadTable.c.origen == origen)
    if tipo_nc:
        query = query.where(QmsNoConformidadTable.c.tipo_nc == tipo_nc)
    if estado:
        query = query.where(QmsNoConformidadTable.c.estado == estado)
    if fecha_desde:
        query = query.where(QmsNoConformidadTable.c.fecha_deteccion >= fecha_desde)
    if fecha_hasta:
        query = query.where(QmsNoConformidadTable.c.fecha_deteccion <= fecha_hasta)
    if buscar:
        search_filter = or_(
            QmsNoConformidadTable.c.numero_nc.ilike(f"%{buscar}%"),
            QmsNoConformidadTable.c.descripcion_nc.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(QmsNoConformidadTable.c.fecha_deteccion.desc())
    return await execute_query(query, client_id=client_id)


async def get_no_conformidad_by_id(client_id: UUID, no_conformidad_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una no conformidad por id."""
    query = select(QmsNoConformidadTable).where(
        and_(
            QmsNoConformidadTable.c.cliente_id == client_id,
            QmsNoConformidadTable.c.no_conformidad_id == no_conformidad_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_no_conformidad(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una no conformidad."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("no_conformidad_id", uuid4())
    stmt = insert(QmsNoConformidadTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_no_conformidad_by_id(client_id, payload["no_conformidad_id"])


async def update_no_conformidad(
    client_id: UUID, no_conformidad_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una no conformidad."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("no_conformidad_id", "cliente_id")
    }
    if not payload:
        return await get_no_conformidad_by_id(client_id, no_conformidad_id)
    stmt = (
        update(QmsNoConformidadTable)
        .where(
            and_(
                QmsNoConformidadTable.c.cliente_id == client_id,
                QmsNoConformidadTable.c.no_conformidad_id == no_conformidad_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_no_conformidad_by_id(client_id, no_conformidad_id)
