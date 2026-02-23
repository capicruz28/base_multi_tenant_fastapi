"""Endpoints BI reportes."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.bi.application.services import (
    list_reporte,
    get_reporte_by_id,
    create_reporte,
    update_reporte,
)
from app.modules.bi.presentation.schemas import (
    ReporteCreate,
    ReporteUpdate,
    ReporteRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ReporteRead])
async def get_reportes(
    empresa_id: Optional[UUID] = Query(None),
    tipo_reporte: Optional[str] = Query(None),
    modulo_origen: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    es_activo: Optional[bool] = Query(None),
    es_publico: Optional[bool] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("bi.reporte.leer")),
):
    return await list_reporte(
        current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_reporte=tipo_reporte,
        modulo_origen=modulo_origen,
        categoria=categoria,
        es_activo=es_activo,
        es_publico=es_publico,
        buscar=buscar,
    )


@router.get("/{reporte_id}", response_model=ReporteRead)
async def get_reporte(
    reporte_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("bi.reporte.leer")),
):
    try:
        return await get_reporte_by_id(current_user.cliente_id, reporte_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ReporteRead, status_code=status.HTTP_201_CREATED)
async def post_reporte(
    data: ReporteCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("bi.reporte.crear")),
):
    return await create_reporte(current_user.cliente_id, data)


@router.put("/{reporte_id}", response_model=ReporteRead)
async def put_reporte(
    reporte_id: UUID,
    data: ReporteUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("bi.reporte.crear")),
):
    try:
        return await update_reporte(current_user.cliente_id, reporte_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
