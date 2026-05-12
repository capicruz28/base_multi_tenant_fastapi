"""
Queries SQLAlchemy Core para prc_lista_precio y prc_lista_precio_detalle.
Filtro tenant estricto: todas las operaciones usan cliente_id;
si se informa empresa_id, se valida en lecturas/actualizaciones.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import PrcListaPrecioTable, PrcListaPrecioDetalleTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS_LISTA = {c.name for c in PrcListaPrecioTable.c}
_COLUMNS_DETALLE = {c.name for c in PrcListaPrecioDetalleTable.c}


def _where_lista_precio(client_id: UUID, lista_precio_id: UUID, empresa_id: Optional[UUID] = None):
    parts = [
        PrcListaPrecioTable.c.cliente_id == client_id,
        PrcListaPrecioTable.c.lista_precio_id == lista_precio_id,
    ]
    if empresa_id is not None:
        parts.append(PrcListaPrecioTable.c.empresa_id == empresa_id)
    return and_(*parts)


def _where_lista_precio_detalle(
    client_id: UUID, lista_precio_detalle_id: UUID, empresa_id: Optional[UUID] = None
):
    parts = [
        PrcListaPrecioDetalleTable.c.cliente_id == client_id,
        PrcListaPrecioDetalleTable.c.lista_precio_detalle_id == lista_precio_detalle_id,
    ]
    if empresa_id is not None:
        parts.append(PrcListaPrecioDetalleTable.c.empresa_id == empresa_id)
    return and_(*parts)


async def list_listas_precio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_lista: Optional[str] = None,
    solo_activos: bool = True,
    solo_vigentes: bool = False,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista listas de precio del tenant. Siempre filtra por cliente_id."""
    query = select(PrcListaPrecioTable).where(PrcListaPrecioTable.c.cliente_id == client_id)
    if empresa_id is not None:
        query = query.where(PrcListaPrecioTable.c.empresa_id == empresa_id)
    if tipo_lista:
        query = query.where(PrcListaPrecioTable.c.tipo_lista == tipo_lista)
    if solo_activos:
        query = query.where(PrcListaPrecioTable.c.es_activo == True)
    if solo_vigentes:
        today = date.today()
        query = query.where(
            and_(
                PrcListaPrecioTable.c.fecha_vigencia_desde <= today,
                or_(
                    PrcListaPrecioTable.c.fecha_vigencia_hasta.is_(None),
                    PrcListaPrecioTable.c.fecha_vigencia_hasta >= today,
                ),
            )
        )
    if buscar:
        search_filter = or_(
            PrcListaPrecioTable.c.nombre.ilike(f"%{buscar}%"),
            PrcListaPrecioTable.c.codigo_lista.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(PrcListaPrecioTable.c.nombre)
    return await execute_query(query, client_id=client_id)


async def get_lista_precio_by_id(
    client_id: UUID, lista_precio_id: UUID, empresa_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """Obtiene una lista de precio por id. Exige cliente_id; opcionalmente empresa_id."""
    query = select(PrcListaPrecioTable).where(_where_lista_precio(client_id, lista_precio_id, empresa_id))
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_lista_precio(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una lista de precio. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS_LISTA}
    payload["cliente_id"] = client_id
    payload.setdefault("lista_precio_id", uuid4())
    stmt = insert(PrcListaPrecioTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_lista_precio_by_id(client_id, payload["lista_precio_id"], None)


async def update_lista_precio(
    client_id: UUID, lista_precio_id: UUID, data: Dict[str, Any], empresa_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """Actualiza una lista de precio. WHERE incluye cliente_id y lista_precio_id; opcionalmente empresa_id."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS_LISTA and k not in ("lista_precio_id", "cliente_id")
    }
    if not payload:
        return await get_lista_precio_by_id(client_id, lista_precio_id, empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(PrcListaPrecioTable)
        .where(_where_lista_precio(client_id, lista_precio_id, empresa_id))
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_lista_precio_by_id(client_id, lista_precio_id, empresa_id)


# ============================================================================
# DETALLES DE LISTA DE PRECIO
# ============================================================================


async def list_lista_precio_detalles(
    client_id: UUID,
    lista_precio_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    solo_activos: bool = True,
    empresa_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """Lista detalles de lista de precio del tenant."""
    query = select(PrcListaPrecioDetalleTable).where(
        PrcListaPrecioDetalleTable.c.cliente_id == client_id
    )
    if empresa_id is not None:
        query = query.where(PrcListaPrecioDetalleTable.c.empresa_id == empresa_id)
    if lista_precio_id:
        query = query.where(PrcListaPrecioDetalleTable.c.lista_precio_id == lista_precio_id)
    if producto_id:
        query = query.where(PrcListaPrecioDetalleTable.c.producto_id == producto_id)
    if solo_activos:
        query = query.where(PrcListaPrecioDetalleTable.c.es_activo == True)
    query = query.order_by(PrcListaPrecioDetalleTable.c.producto_id)
    return await execute_query(query, client_id=client_id)


async def get_lista_precio_detalle_by_id(
    client_id: UUID, lista_precio_detalle_id: UUID, empresa_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """Obtiene un detalle por id. Opcionalmente restringe por empresa_id."""
    query = select(PrcListaPrecioDetalleTable).where(
        _where_lista_precio_detalle(client_id, lista_precio_detalle_id, empresa_id)
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_lista_precio_detalle(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un detalle de lista de precio. empresa_id debe coincidir con la cabecera (validado en servicio)."""
    from uuid import uuid4

    payload = {k: v for k, v in data.items() if k in _COLUMNS_DETALLE}
    payload["cliente_id"] = client_id
    payload.setdefault("lista_precio_detalle_id", uuid4())
    lista_precio_id = payload.get("lista_precio_id")
    if lista_precio_id:
        q = select(PrcListaPrecioTable.c.empresa_id).where(
            and_(
                PrcListaPrecioTable.c.cliente_id == client_id,
                PrcListaPrecioTable.c.lista_precio_id == lista_precio_id,
            )
        )
        rows = await execute_query(q, client_id=client_id)
        if rows:
            payload["empresa_id"] = rows[0]["empresa_id"]
    stmt = insert(PrcListaPrecioDetalleTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_lista_precio_detalle_by_id(client_id, payload["lista_precio_detalle_id"], None)


async def update_lista_precio_detalle(
    client_id: UUID,
    lista_precio_detalle_id: UUID,
    data: Dict[str, Any],
    empresa_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Actualiza un detalle de lista de precio."""
    payload = {
        k: v
        for k, v in data.items()
        if k in _COLUMNS_DETALLE and k not in ("lista_precio_detalle_id", "cliente_id", "empresa_id")
    }
    if not payload:
        return await get_lista_precio_detalle_by_id(client_id, lista_precio_detalle_id, empresa_id)
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(PrcListaPrecioDetalleTable)
        .where(_where_lista_precio_detalle(client_id, lista_precio_detalle_id, empresa_id))
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_lista_precio_detalle_by_id(client_id, lista_precio_detalle_id, empresa_id)
