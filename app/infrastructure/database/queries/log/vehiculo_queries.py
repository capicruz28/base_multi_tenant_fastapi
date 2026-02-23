"""
Queries SQLAlchemy Core para log_vehiculo.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import LogVehiculoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in LogVehiculoTable.c}


async def list_vehiculos(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    transportista_id: Optional[UUID] = None,
    tipo_propiedad: Optional[str] = None,
    estado_vehiculo: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista vehículos del tenant. Siempre filtra por cliente_id."""
    query = select(LogVehiculoTable).where(
        LogVehiculoTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(LogVehiculoTable.c.empresa_id == empresa_id)
    if transportista_id:
        query = query.where(LogVehiculoTable.c.transportista_id == transportista_id)
    if tipo_propiedad:
        query = query.where(LogVehiculoTable.c.tipo_propiedad == tipo_propiedad)
    if estado_vehiculo:
        query = query.where(LogVehiculoTable.c.estado_vehiculo == estado_vehiculo)
    if solo_activos:
        query = query.where(LogVehiculoTable.c.es_activo == True)
    if buscar:
        search_filter = or_(
            LogVehiculoTable.c.placa.ilike(f"%{buscar}%"),
            LogVehiculoTable.c.marca.ilike(f"%{buscar}%"),
            LogVehiculoTable.c.modelo.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(LogVehiculoTable.c.placa)
    return await execute_query(query, client_id=client_id)


async def get_vehiculo_by_id(client_id: UUID, vehiculo_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un vehículo por id. Exige cliente_id para no cruzar tenants."""
    query = select(LogVehiculoTable).where(
        and_(
            LogVehiculoTable.c.cliente_id == client_id,
            LogVehiculoTable.c.vehiculo_id == vehiculo_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_vehiculo(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un vehículo. cliente_id se fuerza desde contexto, no desde data."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("vehiculo_id", uuid4())
    stmt = insert(LogVehiculoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_vehiculo_by_id(client_id, payload["vehiculo_id"])


async def update_vehiculo(
    client_id: UUID, vehiculo_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un vehículo. WHERE incluye cliente_id y vehiculo_id."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("vehiculo_id", "cliente_id")
    }
    if not payload:
        return await get_vehiculo_by_id(client_id, vehiculo_id)
    stmt = (
        update(LogVehiculoTable)
        .where(
            and_(
                LogVehiculoTable.c.cliente_id == client_id,
                LogVehiculoTable.c.vehiculo_id == vehiculo_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_vehiculo_by_id(client_id, vehiculo_id)
