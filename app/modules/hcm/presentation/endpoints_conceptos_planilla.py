"""Endpoints FastAPI para hcm_concepto_planilla."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.hcm.application.services import (
    list_conceptos_planilla,
    get_concepto_planilla_by_id,
    create_concepto_planilla,
    update_concepto_planilla,
)
from app.modules.hcm.presentation.schemas import ConceptoPlanillaCreate, ConceptoPlanillaUpdate, ConceptoPlanillaRead
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ConceptoPlanillaRead], tags=["HCM - Conceptos Planilla"])
async def get_conceptos_planilla(
    empresa_id: Optional[UUID] = Query(None),
    tipo_concepto: Optional[str] = Query(None),
    es_activo: Optional[bool] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_conceptos_planilla(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_concepto=tipo_concepto,
        es_activo=es_activo,
        buscar=buscar,
    )


@router.get("/{concepto_id}", response_model=ConceptoPlanillaRead, tags=["HCM - Conceptos Planilla"])
async def get_concepto_planilla(
    concepto_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_concepto_planilla_by_id(current_user.cliente_id, concepto_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ConceptoPlanillaRead, status_code=status.HTTP_201_CREATED, tags=["HCM - Conceptos Planilla"])
async def post_concepto_planilla(
    data: ConceptoPlanillaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_concepto_planilla(current_user.cliente_id, data)


@router.put("/{concepto_id}", response_model=ConceptoPlanillaRead, tags=["HCM - Conceptos Planilla"])
async def put_concepto_planilla(
    concepto_id: UUID,
    data: ConceptoPlanillaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_concepto_planilla(current_user.cliente_id, concepto_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
