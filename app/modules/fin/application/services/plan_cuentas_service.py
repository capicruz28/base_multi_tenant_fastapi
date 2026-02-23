"""
Servicios de aplicación para fin_plan_cuentas.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.fin import (
    list_plan_cuentas as _list_plan_cuentas,
    get_cuenta_by_id as _get_cuenta_by_id,
    create_cuenta as _create_cuenta,
    update_cuenta as _update_cuenta,
)
from app.modules.fin.presentation.schemas import (
    PlanCuentaCreate,
    PlanCuentaUpdate,
    PlanCuentaRead,
)
from app.core.exceptions import NotFoundError


async def list_plan_cuentas(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    cuenta_padre_id: Optional[UUID] = None,
    tipo_cuenta: Optional[str] = None,
    nivel: Optional[int] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None
) -> List[PlanCuentaRead]:
    """Lista cuentas del plan contable del tenant."""
    rows = await _list_plan_cuentas(
        client_id=client_id,
        empresa_id=empresa_id,
        cuenta_padre_id=cuenta_padre_id,
        tipo_cuenta=tipo_cuenta,
        nivel=nivel,
        solo_activos=solo_activos,
        buscar=buscar
    )
    return [PlanCuentaRead(**row) for row in rows]


async def get_cuenta_by_id(client_id: UUID, cuenta_id: UUID) -> PlanCuentaRead:
    """Obtiene una cuenta por id. Lanza NotFoundError si no existe."""
    row = await _get_cuenta_by_id(client_id, cuenta_id)
    if not row:
        raise NotFoundError(f"Cuenta {cuenta_id} no encontrada")
    return PlanCuentaRead(**row)


async def create_cuenta(client_id: UUID, data: PlanCuentaCreate) -> PlanCuentaRead:
    """Crea una cuenta."""
    row = await _create_cuenta(client_id, data.model_dump(exclude_none=True))
    return PlanCuentaRead(**row)


async def update_cuenta(
    client_id: UUID, cuenta_id: UUID, data: PlanCuentaUpdate
) -> PlanCuentaRead:
    """Actualiza una cuenta. Lanza NotFoundError si no existe."""
    row = await _update_cuenta(
        client_id, cuenta_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Cuenta {cuenta_id} no encontrada")
    return PlanCuentaRead(**row)
