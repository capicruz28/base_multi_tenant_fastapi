"""Endpoints wfl flujo de trabajo."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.wfl.application.services import (
    list_flujo_trabajo,
    get_flujo_trabajo_by_id,
    create_flujo_trabajo,
    update_flujo_trabajo,
)
from app.modules.wfl.presentation.schemas import (
    FlujoTrabajoCreate,
    FlujoTrabajoUpdate,
    FlujoTrabajoRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[FlujoTrabajoRead])
async def get_flujos_trabajo(
    empresa_id: Optional[UUID] = Query(None),
    tipo_flujo: Optional[str] = Query(None),
    modulo_aplicable: Optional[str] = Query(None),
    es_activo: Optional[bool] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("wfl.flujo.leer")),
):
    return await list_flujo_trabajo(
        current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_flujo=tipo_flujo,
        modulo_aplicable=modulo_aplicable,
        es_activo=es_activo,
        buscar=buscar,
    )


@router.get("/{flujo_id}", response_model=FlujoTrabajoRead)
async def get_flujo_trabajo(
    flujo_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("wfl.flujo.leer")),
):
    try:
        return await get_flujo_trabajo_by_id(current_user.cliente_id, flujo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=FlujoTrabajoRead, status_code=status.HTTP_201_CREATED)
async def post_flujo_trabajo(
    data: FlujoTrabajoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("wfl.flujo.crear")),
):
    return await create_flujo_trabajo(current_user.cliente_id, data)


@router.put("/{flujo_id}", response_model=FlujoTrabajoRead)
async def put_flujo_trabajo(
    flujo_id: UUID,
    data: FlujoTrabajoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("wfl.flujo.actualizar")),
):
    try:
        return await update_flujo_trabajo(current_user.cliente_id, flujo_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
