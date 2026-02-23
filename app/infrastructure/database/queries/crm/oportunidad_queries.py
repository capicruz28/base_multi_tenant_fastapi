"""
Queries SQLAlchemy Core para crm_oportunidad.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date, datetime
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import CrmOportunidadTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in CrmOportunidadTable.c}


async def list_oportunidades(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    cliente_venta_id: Optional[UUID] = None,
    lead_id: Optional[UUID] = None,
    campana_id: Optional[UUID] = None,
    vendedor_usuario_id: Optional[UUID] = None,
    etapa: Optional[str] = None,
    estado: Optional[str] = None,
    tipo_oportunidad: Optional[str] = None,
    fecha_cierre_desde: Optional[date] = None,
    fecha_cierre_hasta: Optional[date] = None,
    buscar: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista oportunidades del tenant."""
    query = select(CrmOportunidadTable).where(
        CrmOportunidadTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(CrmOportunidadTable.c.empresa_id == empresa_id)
    if cliente_venta_id:
        query = query.where(CrmOportunidadTable.c.cliente_venta_id == cliente_venta_id)
    if lead_id:
        query = query.where(CrmOportunidadTable.c.lead_id == lead_id)
    if campana_id:
        query = query.where(CrmOportunidadTable.c.campana_id == campana_id)
    if vendedor_usuario_id:
        query = query.where(CrmOportunidadTable.c.vendedor_usuario_id == vendedor_usuario_id)
    if etapa:
        query = query.where(CrmOportunidadTable.c.etapa == etapa)
    if estado:
        query = query.where(CrmOportunidadTable.c.estado == estado)
    if tipo_oportunidad:
        query = query.where(CrmOportunidadTable.c.tipo_oportunidad == tipo_oportunidad)
    if fecha_cierre_desde:
        query = query.where(CrmOportunidadTable.c.fecha_cierre_estimada >= fecha_cierre_desde)
    if fecha_cierre_hasta:
        query = query.where(CrmOportunidadTable.c.fecha_cierre_estimada <= fecha_cierre_hasta)
    if buscar:
        search_filter = or_(
            CrmOportunidadTable.c.nombre.ilike(f"%{buscar}%"),
            CrmOportunidadTable.c.numero_oportunidad.ilike(f"%{buscar}%"),
            CrmOportunidadTable.c.nombre_cliente_prospecto.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(CrmOportunidadTable.c.fecha_cierre_estimada, CrmOportunidadTable.c.fecha_creacion.desc())
    return await execute_query(query, client_id=client_id)


async def get_oportunidad_by_id(client_id: UUID, oportunidad_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene una oportunidad por id."""
    query = select(CrmOportunidadTable).where(
        and_(
            CrmOportunidadTable.c.cliente_id == client_id,
            CrmOportunidadTable.c.oportunidad_id == oportunidad_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_oportunidad(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta una oportunidad."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("oportunidad_id", uuid4())
    stmt = insert(CrmOportunidadTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_oportunidad_by_id(client_id, payload["oportunidad_id"])


async def update_oportunidad(
    client_id: UUID, oportunidad_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza una oportunidad."""
    from datetime import datetime
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("oportunidad_id", "cliente_id")
    }
    if not payload:
        return await get_oportunidad_by_id(client_id, oportunidad_id)
    # Actualizar fecha_actualizacion si hay cambios
    payload["fecha_actualizacion"] = datetime.utcnow()
    stmt = (
        update(CrmOportunidadTable)
        .where(
            and_(
                CrmOportunidadTable.c.cliente_id == client_id,
                CrmOportunidadTable.c.oportunidad_id == oportunidad_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_oportunidad_by_id(client_id, oportunidad_id)
