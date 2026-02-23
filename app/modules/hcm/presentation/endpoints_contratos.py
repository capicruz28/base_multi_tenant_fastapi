"""Endpoints FastAPI para hcm_contrato."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.hcm.application.services import (
    list_contratos,
    get_contrato_by_id,
    create_contrato,
    update_contrato,
)
from app.modules.hcm.presentation.schemas import ContratoCreate, ContratoUpdate, ContratoRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ContratoRead], tags=["HCM - Contratos"])
async def get_contratos(
    empresa_id: Optional[UUID] = Query(None),
    empleado_id: Optional[UUID] = Query(None),
    estado_contrato: Optional[str] = Query(None),
    es_contrato_vigente: Optional[bool] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_contratos(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        empleado_id=empleado_id,
        estado_contrato=estado_contrato,
        es_contrato_vigente=es_contrato_vigente,
    )


@router.get("/{contrato_id}", response_model=ContratoRead, tags=["HCM - Contratos"])
async def get_contrato(
    contrato_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_contrato_by_id(current_user.cliente_id, contrato_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ContratoRead, status_code=status.HTTP_201_CREATED, tags=["HCM - Contratos"])
async def post_contrato(
    data: ContratoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_contrato(current_user.cliente_id, data)


@router.put("/{contrato_id}", response_model=ContratoRead, tags=["HCM - Contratos"])
async def put_contrato(
    contrato_id: UUID,
    data: ContratoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_contrato(current_user.cliente_id, contrato_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
