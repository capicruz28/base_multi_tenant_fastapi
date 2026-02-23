"""
Queries SQLAlchemy Core para hcm_concepto_planilla.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import HcmConceptoPlanillaTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in HcmConceptoPlanillaTable.c}


async def list_conceptos_planilla(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_concepto: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista conceptos de planilla del tenant."""
    query = select(HcmConceptoPlanillaTable).where(
        HcmConceptoPlanillaTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(HcmConceptoPlanillaTable.c.empresa_id == empresa_id)
    if tipo_concepto:
        query = query.where(HcmConceptoPlanillaTable.c.tipo_concepto == tipo_concepto)
    if es_activo is not None:
        query = query.where(HcmConceptoPlanillaTable.c.es_activo == es_activo)
    if buscar:
        search_filter = or_(
            HcmConceptoPlanillaTable.c.nombre.ilike(f"%{buscar}%"),
            HcmConceptoPlanillaTable.c.codigo_concepto.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(HcmConceptoPlanillaTable.c.tipo_concepto, HcmConceptoPlanillaTable.c.codigo_concepto)
    return await execute_query(query, client_id=client_id)


async def get_concepto_planilla_by_id(client_id: UUID, concepto_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un concepto de planilla por id."""
    query = select(HcmConceptoPlanillaTable).where(
        and_(
            HcmConceptoPlanillaTable.c.cliente_id == client_id,
            HcmConceptoPlanillaTable.c.concepto_id == concepto_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_concepto_planilla(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un concepto de planilla."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("concepto_id", uuid4())
    stmt = insert(HcmConceptoPlanillaTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_concepto_planilla_by_id(client_id, payload["concepto_id"])


async def update_concepto_planilla(
    client_id: UUID, concepto_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un concepto de planilla."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("concepto_id", "cliente_id")
    }
    if not payload:
        return await get_concepto_planilla_by_id(client_id, concepto_id)
    stmt = (
        update(HcmConceptoPlanillaTable)
        .where(
            and_(
                HcmConceptoPlanillaTable.c.cliente_id == client_id,
                HcmConceptoPlanillaTable.c.concepto_id == concepto_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_concepto_planilla_by_id(client_id, concepto_id)
