"""
Endpoints FastAPI para fin_plan_cuentas.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.fin.application.services import (
    list_plan_cuentas,
    get_cuenta_by_id,
    create_cuenta,
    update_cuenta,
    desactivar_cuenta,
    reactivar_cuenta,
)
from app.modules.fin.presentation.schemas import (
    PlanCuentaCreate,
    PlanCuentaUpdate,
    PlanCuentaRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()

MODULE_CODE = "fin"
RESOURCE_CODE = "plan_cuenta"


@router.get("", response_model=List[PlanCuentaRead], tags=["FIN - Plan de Cuentas"])
async def get_plan_cuentas(
    empresa_id: Optional[UUID] = Query(None),
    cuenta_padre_id: Optional[UUID] = Query(None),
    tipo_cuenta: Optional[str] = Query(None),
    nivel: Optional[int] = Query(None),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
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
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
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
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una cuenta."""
    return await create_cuenta(current_user.cliente_id, data)


@router.put("/{cuenta_id}", response_model=PlanCuentaRead, tags=["FIN - Plan de Cuentas"])
async def put_cuenta(
    cuenta_id: UUID,
    data: PlanCuentaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una cuenta."""
    try:
        return await update_cuenta(current_user.cliente_id, cuenta_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{cuenta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["FIN - Plan de Cuentas"],
    summary="Baja lógica de cuenta (es_activo=0)",
)
async def delete_cuenta(
    cuenta_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.eliminar")),
):
    """Marca la cuenta como inactiva dentro del tenant."""
    try:
        await desactivar_cuenta(current_user.cliente_id, cuenta_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{cuenta_id}/reactivar",
    response_model=PlanCuentaRead,
    tags=["FIN - Plan de Cuentas"],
    summary="Reactivar cuenta del plan",
)
async def post_reactivar_cuenta(
    cuenta_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Reactiva una cuenta previamente dada de baja."""
    try:
        return await reactivar_cuenta(current_user.cliente_id, cuenta_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
