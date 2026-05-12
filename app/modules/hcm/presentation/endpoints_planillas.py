"""Endpoints FastAPI para hcm_planilla."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.hcm.application.services import (
    list_planillas,
    get_planilla_by_id,
    create_planilla,
    update_planilla,
    calcular_planilla,
    aprobar_planilla,
    marcar_pagada_planilla,
    cerrar_planilla,
)
from app.modules.hcm.presentation.schemas import PlanillaCreate, PlanillaUpdate, PlanillaRead
from app.core.exceptions import NotFoundError

router = APIRouter()

MODULE_CODE = "hcm"
RESOURCE_CODE = "planilla"


@router.get("", response_model=List[PlanillaRead], tags=["HCM - Planillas"])
async def get_planillas(
    empresa_id: Optional[UUID] = Query(None),
    tipo_planilla: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    año: Optional[int] = Query(None),
    mes: Optional[int] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    return await list_planillas(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_planilla=tipo_planilla,
        estado=estado,
        año=año,
        mes=mes,
    )


@router.get("/{planilla_id}", response_model=PlanillaRead, tags=["HCM - Planillas"])
async def get_planilla(
    planilla_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    try:
        return await get_planilla_by_id(current_user.cliente_id, planilla_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PlanillaRead, status_code=status.HTTP_201_CREATED, tags=["HCM - Planillas"])
async def post_planilla(
    data: PlanillaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    return await create_planilla(current_user.cliente_id, data)


@router.put("/{planilla_id}", response_model=PlanillaRead, tags=["HCM - Planillas"])
async def put_planilla(
    planilla_id: UUID,
    data: PlanillaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    try:
        return await update_planilla(current_user.cliente_id, planilla_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{planilla_id}/calcular",
    response_model=PlanillaRead,
    tags=["HCM - Planillas"],
    summary="Calcular planilla (borrador → calculada)",
)
async def post_calcular_planilla(
    planilla_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.calcular")
    ),
):
    try:
        return await calcular_planilla(current_user.cliente_id, planilla_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{planilla_id}/aprobar",
    response_model=PlanillaRead,
    tags=["HCM - Planillas"],
    summary="Aprobar planilla (calculada → aprobada)",
)
async def post_aprobar_planilla(
    planilla_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.aprobar")
    ),
):
    try:
        return await aprobar_planilla(
            current_user.cliente_id,
            planilla_id,
            aprobado_por_usuario_id=current_user.usuario_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{planilla_id}/marcar-pagada",
    response_model=PlanillaRead,
    tags=["HCM - Planillas"],
    summary="Marcar planilla como pagada (aprobada → pagada)",
)
async def post_marcar_pagada_planilla(
    planilla_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.marcar-pagada")
    ),
):
    try:
        return await marcar_pagada_planilla(current_user.cliente_id, planilla_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{planilla_id}/cerrar",
    response_model=PlanillaRead,
    tags=["HCM - Planillas"],
    summary="Cerrar planilla (pagada → cerrada)",
)
async def post_cerrar_planilla(
    planilla_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.cerrar")
    ),
):
    try:
        return await cerrar_planilla(current_user.cliente_id, planilla_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
