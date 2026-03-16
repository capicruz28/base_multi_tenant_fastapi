"""Endpoints mps_pronostico_demanda."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.mps.application.services import (
    list_pronostico_demanda,
    get_pronostico_demanda_by_id,
    create_pronostico_demanda,
    update_pronostico_demanda,
)
from app.modules.mps.presentation.schemas import (
    PronosticoDemandaCreate,
    PronosticoDemandaUpdate,
    PronosticoDemandaRead,
)
from app.core.exceptions import NotFoundError

MODULE_CODE = "mps"
RESOURCE_CODE = "pronostico_demanda"

router = APIRouter()


@router.get("", response_model=List[PronosticoDemandaRead], tags=["MPS - Pronóstico Demanda"])
async def get_pronosticos_demanda(
    empresa_id: Optional[UUID] = Query(None),
    producto_id: Optional[UUID] = Query(None),
    anio: Optional[int] = Query(None),
    mes: Optional[int] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    return await list_pronostico_demanda(
        current_user.cliente_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        anio=anio,
        mes=mes,
    )


@router.get("/{pronostico_id}", response_model=PronosticoDemandaRead, tags=["MPS - Pronóstico Demanda"])
async def get_pronostico_demanda(
    pronostico_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    try:
        return await get_pronostico_demanda_by_id(current_user.cliente_id, pronostico_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PronosticoDemandaRead, status_code=status.HTTP_201_CREATED, tags=["MPS - Pronóstico Demanda"])
async def post_pronostico_demanda(
    data: PronosticoDemandaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    return await create_pronostico_demanda(current_user.cliente_id, data)


@router.put("/{pronostico_id}", response_model=PronosticoDemandaRead, tags=["MPS - Pronóstico Demanda"])
async def put_pronostico_demanda(
    pronostico_id: UUID,
    data: PronosticoDemandaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    try:
        return await update_pronostico_demanda(current_user.cliente_id, pronostico_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
