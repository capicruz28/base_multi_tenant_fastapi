"""Queries para dms_documento. Filtro tenant: cliente_id."""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, insert, update, and_, or_
from app.infrastructure.database.tables_erp import DmsDocumentoTable
from app.infrastructure.database.queries_async import execute_query, execute_insert, execute_update

_COLUMNS = {c.name for c in DmsDocumentoTable.c}


async def list_documento(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_documento: Optional[str] = None,
    categoria: Optional[str] = None,
    estado: Optional[str] = None,
    entidad_tipo: Optional[str] = None,
    entidad_id: Optional[UUID] = None,
    carpeta: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[Dict[str, Any]]:
    q = select(DmsDocumentoTable).where(DmsDocumentoTable.c.cliente_id == client_id)
    if empresa_id:
        q = q.where(DmsDocumentoTable.c.empresa_id == empresa_id)
    if tipo_documento:
        q = q.where(DmsDocumentoTable.c.tipo_documento == tipo_documento)
    if categoria:
        q = q.where(DmsDocumentoTable.c.categoria == categoria)
    if estado:
        q = q.where(DmsDocumentoTable.c.estado == estado)
    if entidad_tipo:
        q = q.where(DmsDocumentoTable.c.entidad_tipo == entidad_tipo)
    if entidad_id:
        q = q.where(DmsDocumentoTable.c.entidad_id == entidad_id)
    if carpeta:
        q = q.where(DmsDocumentoTable.c.carpeta == carpeta)
    if buscar:
        q = q.where(or_(
            DmsDocumentoTable.c.nombre_archivo.ilike(f"%{buscar}%"),
            DmsDocumentoTable.c.codigo_documento.ilike(f"%{buscar}%"),
            DmsDocumentoTable.c.descripcion.ilike(f"%{buscar}%"),
        ))
    q = q.order_by(DmsDocumentoTable.c.fecha_creacion.desc(), DmsDocumentoTable.c.nombre_archivo)
    return await execute_query(q, client_id=client_id)


async def get_documento_by_id(client_id: UUID, documento_id: UUID) -> Optional[Dict[str, Any]]:
    q = select(DmsDocumentoTable).where(
        and_(
            DmsDocumentoTable.c.cliente_id == client_id,
            DmsDocumentoTable.c.documento_id == documento_id,
        )
    )
    rows = await execute_query(q, client_id=client_id)
    return rows[0] if rows else None


async def create_documento(client_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    from uuid import uuid4
    payload = {k: v for k, v in data.items() if k in _COLUMNS}
    payload["cliente_id"] = client_id
    payload.setdefault("documento_id", uuid4())
    await execute_insert(insert(DmsDocumentoTable).values(**payload), client_id=client_id)
    return await get_documento_by_id(client_id, payload["documento_id"])


async def update_documento(
    client_id: UUID, documento_id: UUID, data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    payload = {
        k: v for k, v in data.items()
        if k in _COLUMNS and k not in ("documento_id", "cliente_id")
    }
    if not payload:
        return await get_documento_by_id(client_id, documento_id)
    stmt = update(DmsDocumentoTable).where(
        and_(
            DmsDocumentoTable.c.cliente_id == client_id,
            DmsDocumentoTable.c.documento_id == documento_id,
        )
    ).values(**payload)
    await execute_update(stmt, client_id=client_id)
    return await get_documento_by_id(client_id, documento_id)
