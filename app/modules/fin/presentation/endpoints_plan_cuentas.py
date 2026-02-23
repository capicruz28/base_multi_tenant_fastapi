"""
Endpoints FastAPI para fin_plan_cuentas.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.fin.application.services import (
    list_plan_cuentas,
    get_cuenta_by_id,
    create_cuenta,
    update_cuenta,
)
from app.modules.fin.presentation.schemas import (
    PlanCuentaCreate,
    PlanCuentaUpdate,
    PlanCuentaRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PlanCuentaRead], tags=["FIN - Plan de Cuentas"])
async def get_plan_cuentas(
    empresa_id: Optional[UUID] = Query(None),
    cuenta_padre_id: Optional[UUID] = Query(None),
    tipo_cuenta: Optional[str] = Query(None),
    nivel: Optional[int] = Query(None),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista cuentas del plan contable del tenant."""
    return await list_plan_cuentas(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        cuenta_padre_id=cuenta_padre_id,
        tipo_cuenta=tipo_cuenta,
        nivel=nivel,
        solo_activos=solo_activos,
        buscar=buscar
    )


@router.get("/{cuenta_id}", response_model=PlanCuentaRead, tags=["FIN - Plan de Cuentas"])
async def get_cuenta(
    cuenta_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene una cuenta por id."""
    try:
        return await get_cuenta_by_id(current_user.cliente_id, cuenta_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PlanCuentaRead, status_code=status.HTTP_201_CREATED, tags=["FIN - Plan de Cuentas"])
async def post_cuenta(
    data: PlanCuentaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una cuenta."""
    return await create_cuenta(current_user.cliente_id, data)


@router.put("/{cuenta_id}", response_model=PlanCuentaRead, tags=["FIN - Plan de Cuentas"])
async def put_cuenta(
    cuenta_id: UUID,
    data: PlanCuentaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza una cuenta."""
    try:
        return await update_cuenta(current_user.cliente_id, cuenta_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
