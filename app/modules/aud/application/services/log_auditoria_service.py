# app/modules/aud/application/services/log_auditoria_service.py
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.infrastructure.database.queries.aud import (
    list_log_auditoria as _list,
    get_log_auditoria_by_id as _get,
    create_log_auditoria as _create,
)
from app.modules.aud.presentation.schemas import (
    LogAuditoriaCreate,
    LogAuditoriaRead,
)
from app.core.exceptions import NotFoundError


async def list_log_auditoria(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    modulo: Optional[str] = None,
    tabla: Optional[str] = None,
    accion: Optional[str] = None,
    usuario_id: Optional[UUID] = None,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    registro_id: Optional[UUID] = None,
    buscar: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[LogAuditoriaRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        modulo=modulo,
        tabla=tabla,
        accion=accion,
        usuario_id=usuario_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        registro_id=registro_id,
        buscar=buscar,
        limit=limit,
    )
    return [LogAuditoriaRead(**dict(r)) for r in rows]


async def get_log_auditoria_by_id(client_id: UUID, log_id: UUID) -> LogAuditoriaRead:
    row = await _get(client_id, log_id)
    if not row:
        raise NotFoundError("Log de auditoría no encontrado")
    return LogAuditoriaRead(**dict(row))


async def create_log_auditoria(client_id: UUID, data: LogAuditoriaCreate) -> LogAuditoriaRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, dump)
    return LogAuditoriaRead(**dict(row))
