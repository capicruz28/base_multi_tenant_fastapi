"""
Queries SQLAlchemy Core para prc_promocion.
Filtro tenant estricto: todas las operaciones usan cliente_id;
si se informa empresa_id, se valida en lecturas/actualizaciones.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import PrcPromocionTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in PrcPromocionTable.c}


def _where_promocion(client_id: UUID, promocion_id: UUID, empresa_id: Optional[UUID] = None):
    parts = [
        PrcPromocionTable.c.cliente_id == client_id,
        PrcPromocionTable.c.promocion_id == promocion_id,
    ]
    if empresa_id is not None:
        parts.append(PrcPromocionTable.c.empresa_id == empresa_id)
    return and_(*parts)


async def list_promociones(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_promocion: Optional[str] = None,
    aplica_a: Optional[str] = None,
    producto_id: Optional[UUID] = None,
    categoria_id: Optional[UUID] = None,
    solo_activos: bool = True,
    solo_vigentes: bool = False,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista promociones del tenant. Siempre filtra por cliente_id."""
    query = select(PrcPromocionTable).where(PrcPromocionTable.c.cliente_id == client_id)
    if empresa_id is not None:
        query = query.where(PrcPromocionTable.c.empresa_id == empresa_id)
    if tipo_promocion:
        query = query.where(PrcPromocionTable.c.tipo_promocion == tipo_promocion)
    if aplica_a:
        query = query.where(PrcPromocionTable.c.aplica_a == aplica_a)
    if producto_id:
        query = query.where(PrcPromocionTable.c.producto_id == producto_id)
    if categoria_id:
        query = query.where(PrcPromocionTable.c.categoria_id == categoria_id)
    if solo_activos:
        query = query.where(PrcPromocionTable.c.es_activo == True)
    if solo_vigentes:
        today = date.today()
        query = query.where(
            and_(
                PrcPromocionTable.c.fecha_inicio <= today,
                PrcPromocionTable.c.fecha_fin >= today,
            )
        )
    if buscar:
        search_filter = or_(
            PrcPromocionTable.c.nombre.ilike(f"%{buscar}%"),
            PrcPromocionTable.c.codigo_promocion.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(PrcPromocionTable.c.fecha_inicio.desc())
    return await execute_query(query, client_id=client_id)


async def get_promocion_by_id(
    client_id: UUID, promocion_id: UUID, empresa_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """Obtiene una promoción por id. Exige cliente_id; opcionalmente empresa_id."""
    query = select(PrcPromocionTable).where(_where_promocion(client_id, promocion_id, empresa_id))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_promocion(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una promoción. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("promocion_id", uuid4())
    stmt = insert(PrcPromocionTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_promocion_by_id(client_id, payload["promocion_id"], None)


async def update_promocion(
    client_id: UUID, promocion_id: UUID, data: Dict[str, Any], empresa_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """Actualiza una promoción. WHERE incluye cliente_id y promocion_id; opcionalmente empresa_id."""
    payload = {
        k: v for k, v in data.items() if k in _COLUMNS and k not in ("promocion_id", "cliente_id")
    }
    if not payload:
        return await get_promocion_by_id(client_id, promocion_id, empresa_id)
    stmt = (
        update(PrcPromocionTable)
        .where(_where_promocion(client_id, promocion_id, empresa_id))
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_promocion_by_id(client_id, promocion_id, empresa_id)
