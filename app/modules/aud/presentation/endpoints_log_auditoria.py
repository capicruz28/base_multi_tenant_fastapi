"""Endpoints AUD log de auditoría (consulta + registro)."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.aud.application.services import (
    list_log_auditoria,
    get_log_auditoria_by_id,
    create_log_auditoria,
)
from app.modules.aud.presentation.schemas import (
    LogAuditoriaCreate,
    LogAuditoriaRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[LogAuditoriaRead])
async def get_logs_auditoria(
    empresa_id: Optional[UUID] = Query(None),
    modulo: Optional[str] = Query(None),
    tabla: Optional[str] = Query(None),
    accion: Optional[str] = Query(None),
    usuario_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    registro_id: Optional[UUID] = Query(None),
    buscar: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=1000),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("aud.log.leer")),
):
    return await list_log_auditoria(
        current_user.cliente_id,
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


@router.get("/{log_id}", response_model=LogAuditoriaRead)
async def get_log_auditoria(
    log_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("aud.log.leer")),
):
    try:
        return await get_log_auditoria_by_id(current_user.cliente_id, log_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=LogAuditoriaRead, status_code=status.HTTP_201_CREATED)
async def post_log_auditoria(
    data: LogAuditoriaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("aud.log.leer")),
):
    return await create_log_auditoria(current_user.cliente_id, data)
