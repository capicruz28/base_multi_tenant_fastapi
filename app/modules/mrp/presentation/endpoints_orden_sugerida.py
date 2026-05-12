"""Endpoints mrp_orden_sugerida."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from pydantic import BaseModel, Field
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mrp.application.services import (
    list_orden_sugerida,
    get_orden_sugerida_by_id,
    create_orden_sugerida,
    update_orden_sugerida,
    aprobar_orden_sugerida,
    rechazar_orden_sugerida,
    convertir_orden_sugerida,
)
from app.modules.mrp.presentation.schemas import OrdenSugeridaCreate, OrdenSugeridaUpdate, OrdenSugeridaRead
from app.core.exceptions import NotFoundError, ValidationError


class ConvertirOrdenSugeridaBody(BaseModel):
    documento_generado_tipo: str = Field(..., max_length=20)
    documento_generado_id: UUID

MODULE_CODE = "mrp"
RESOURCE_CODE = "orden_sugerida"

router = APIRouter()


@router.get("", response_model=List[OrdenSugeridaRead], tags=["MRP - Órdenes Sugeridas"])
async def get_ordenes_sugeridas(
    plan_maestro_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    tipo_orden: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    return await list_orden_sugerida(
        current_user.cliente_id,
        plan_maestro_id=plan_maestro_id,
        producto_id=producto_id,
        estado=estado,
        tipo_orden=tipo_orden,
    )


@router.get("/{orden_sugerida_id}", response_model=OrdenSugeridaRead, tags=["MRP - Órdenes Sugeridas"])
async def get_orden_sugerida(
    orden_sugerida_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    try:
        return await get_orden_sugerida_by_id(current_user.cliente_id, orden_sugerida_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=OrdenSugeridaRead, status_code=status.HTTP_201_CREATED, tags=["MRP - Órdenes Sugeridas"])
async def post_orden_sugerida(
    data: OrdenSugeridaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    return await create_orden_sugerida(current_user.cliente_id, data)


@router.put("/{orden_sugerida_id}", response_model=OrdenSugeridaRead, tags=["MRP - Órdenes Sugeridas"])
async def put_orden_sugerida(
    orden_sugerida_id: UUID,
    data: OrdenSugeridaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    try:
        return await update_orden_sugerida(current_user.cliente_id, orden_sugerida_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{orden_sugerida_id}/aprobar",
    response_model=OrdenSugeridaRead,
    tags=["MRP - Órdenes Sugeridas"],
)
async def post_orden_sugerida_aprobar(
    orden_sugerida_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.aprobar")),
):
    try:
        return await aprobar_orden_sugerida(current_user.cliente_id, orden_sugerida_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{orden_sugerida_id}/rechazar",
    response_model=OrdenSugeridaRead,
    tags=["MRP - Órdenes Sugeridas"],
)
async def post_orden_sugerida_rechazar(
    orden_sugerida_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.rechazar")),
):
    try:
        return await rechazar_orden_sugerida(current_user.cliente_id, orden_sugerida_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{orden_sugerida_id}/convertir",
    response_model=OrdenSugeridaRead,
    tags=["MRP - Órdenes Sugeridas"],
)
async def post_orden_sugerida_convertir(
    orden_sugerida_id: UUID,
    body: ConvertirOrdenSugeridaBody = Body(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.convertir")),
):
    try:
        return await convertir_orden_sugerida(
            current_user.cliente_id,
            orden_sugerida_id,
            documento_generado_tipo=body.documento_generado_tipo,
            documento_generado_id=body.documento_generado_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
