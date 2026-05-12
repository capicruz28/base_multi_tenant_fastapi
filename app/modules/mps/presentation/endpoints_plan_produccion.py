"""Endpoints mps_plan_produccion."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mps.application.services import (
    list_plan_produccion,
    get_plan_produccion_by_id,
    create_plan_produccion,
    update_plan_produccion,
    aprobar_plan_produccion,
    ejecutar_plan_produccion,
    cerrar_plan_produccion,
    anular_plan_produccion,
)
from app.modules.mps.presentation.schemas import PlanProduccionCreate, PlanProduccionUpdate, PlanProduccionRead
from app.core.exceptions import NotFoundError, ValidationError

MODULE_CODE = "mps"
RESOURCE_CODE = "plan_produccion"

router = APIRouter()


@router.get("", response_model=List[PlanProduccionRead], tags=["MPS - Plan de Producción"])
async def get_planes_produccion(
    empresa_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    return await list_plan_produccion(
        current_user.cliente_id,
        empresa_id=empresa_id,
        estado=estado,
        buscar=buscar,
    )


@router.get("/{plan_produccion_id}", response_model=PlanProduccionRead, tags=["MPS - Plan de Producción"])
async def get_plan_produccion(
    plan_produccion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    try:
        return await get_plan_produccion_by_id(current_user.cliente_id, plan_produccion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PlanProduccionRead, status_code=status.HTTP_201_CREATED, tags=["MPS - Plan de Producción"])
async def post_plan_produccion(
    data: PlanProduccionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    return await create_plan_produccion(current_user.cliente_id, data)


@router.put("/{plan_produccion_id}", response_model=PlanProduccionRead, tags=["MPS - Plan de Producción"])
async def put_plan_produccion(
    plan_produccion_id: UUID,
    data: PlanProduccionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    try:
        return await update_plan_produccion(current_user.cliente_id, plan_produccion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{plan_produccion_id}/aprobar",
    response_model=PlanProduccionRead,
    tags=["MPS - Plan de Producción"],
)
async def post_plan_produccion_aprobar(
    plan_produccion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.aprobar")),
):
    try:
        return await aprobar_plan_produccion(current_user.cliente_id, plan_produccion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{plan_produccion_id}/ejecutar",
    response_model=PlanProduccionRead,
    tags=["MPS - Plan de Producción"],
)
async def post_plan_produccion_ejecutar(
    plan_produccion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.ejecutar")),
):
    try:
        return await ejecutar_plan_produccion(current_user.cliente_id, plan_produccion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{plan_produccion_id}/cerrar",
    response_model=PlanProduccionRead,
    tags=["MPS - Plan de Producción"],
)
async def post_plan_produccion_cerrar(
    plan_produccion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.cerrar")),
):
    try:
        return await cerrar_plan_produccion(current_user.cliente_id, plan_produccion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{plan_produccion_id}/anular",
    response_model=PlanProduccionRead,
    tags=["MPS - Plan de Producción"],
)
async def post_plan_produccion_anular(
    plan_produccion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.anular")),
):
    try:
        return await anular_plan_produccion(current_user.cliente_id, plan_produccion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
