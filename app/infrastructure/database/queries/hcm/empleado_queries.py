"""
Queries SQLAlchemy Core para hcm_empleado.
Filtro tenant estricto: todas las operaciones usan cliente_id.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date
from sqlalchemy import select, insert, update, and_, or_

from app.infrastructure.database.tables_erp import HcmEmpleadoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in HcmEmpleadoTable.c}


async def list_empleados(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado_empleado: Optional[str] = None,
    es_activo: Optional[bool] = None,
    departamento_id: Optional[UUID] = None,
    cargo_id: Optional[UUID] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lista empleados del tenant."""
    query = select(HcmEmpleadoTable).where(
        HcmEmpleadoTable.c.cliente_id == client_id
    )
    if empresa_id:
        query = query.where(HcmEmpleadoTable.c.empresa_id == empresa_id)
    if estado_empleado:
        query = query.where(HcmEmpleadoTable.c.estado_empleado == estado_empleado)
    if es_activo is not None:
        query = query.where(HcmEmpleadoTable.c.es_activo == es_activo)
    if departamento_id:
        query = query.where(HcmEmpleadoTable.c.departamento_id == departamento_id)
    if cargo_id:
        query = query.where(HcmEmpleadoTable.c.cargo_id == cargo_id)
    if buscar:
        search_filter = or_(
            HcmEmpleadoTable.c.nombres.ilike(f"%{buscar}%"),
            HcmEmpleadoTable.c.apellido_paterno.ilike(f"%{buscar}%"),
            HcmEmpleadoTable.c.apellido_materno.ilike(f"%{buscar}%"),
            HcmEmpleadoTable.c.codigo_empleado.ilike(f"%{buscar}%"),
            HcmEmpleadoTable.c.numero_documento.ilike(f"%{buscar}%"),
        )
        query = query.where(search_filter)
    query = query.order_by(
        HcmEmpleadoTable.c.apellido_paterno,
        HcmEmpleadoTable.c.apellido_materno,
        HcmEmpleadoTable.c.nombres,
    )
    return await execute_query(query, client_id=client_id)


async def get_empleado_by_id(client_id: UUID, empleado_id: UUID) -> Optional[Dict[str, Any]]:
    """Obtiene un empleado por id."""
    query = select(HcmEmpleadoTable).where(
        and_(
            HcmEmpleadoTable.c.cliente_id == client_id,
            HcmEmpleadoTable.c.empleado_id == empleado_id,
        )
    )
    rows = await execute_query(query, client_id=client_id)
    return rows[0] if rows else None


async def create_empleado(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Inserta un empleado."""
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("empleado_id", uuid4())
    stmt = insert(HcmEmpleadoTable).values(**payload)
    await execute_insert(stmt, client_id=client_id)
    return await get_empleado_by_id(client_id, payload["empleado_id"])


async def update_empleado(
    client_id: UUID, empleado_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Actualiza un empleado."""
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("empleado_id", "cliente_id")
    }
    if not payload:
        return await get_empleado_by_id(client_id, empleado_id)
    stmt = (
        update(HcmEmpleadoTable)
        .where(
            and_(
                HcmEmpleadoTable.c.cliente_id == client_id,
                HcmEmpleadoTable.c.empleado_id == empleado_id,
            )
        )
        .values(**payload)
    )
    await execute_update(stmt, client_id=client_id)
    return await get_empleado_by_id(client_id, empleado_id)
