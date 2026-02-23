"""
Servicios de aplicación para fin_periodo_contable.
Maneja la lógica de negocio y llama a las queries.
"""
from typing import List, Optional
from uuid import UUID

from app.infrastructure.database.queries.fin import (
    list_periodos_contables as _list_periodos_contables,
    get_periodo_contable_by_id as _get_periodo_contable_by_id,
    create_periodo_contable as _create_periodo_contable,
    update_periodo_contable as _update_periodo_contable,
)
from app.modules.fin.presentation.schemas import (
    PeriodoContableCreate,
    PeriodoContableUpdate,
    PeriodoContableRead,
)
from app.core.exceptions import NotFoundError


async def list_periodos_contables(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    año: Optional[int] = None,
    mes: Optional[int] = None,
    estado: Optional[str] = None
) -> List[PeriodoContableRead]:
    """Lista periodos contables del tenant."""
    rows = await _list_periodos_contables(
        client_id=client_id,
        empresa_id=empresa_id,
        año=año,
        mes=mes,
        estado=estado
    )
    return [PeriodoContableRead(**row) for row in rows]


async def get_periodo_contable_by_id(client_id: UUID, periodo_id: UUID) -> PeriodoContableRead:
    """Obtiene un periodo contable por id. Lanza NotFoundError si no existe."""
    row = await _get_periodo_contable_by_id(client_id, periodo_id)
    if not row:
        raise NotFoundError(f"Periodo contable {periodo_id} no encontrado")
    return PeriodoContableRead(**row)


async def create_periodo_contable(client_id: UUID, data: PeriodoContableCreate) -> PeriodoContableRead:
    """Crea un periodo contable."""
    row = await _create_periodo_contable(client_id, data.model_dump(exclude_none=True))
    return PeriodoContableRead(**row)


async def update_periodo_contable(
    client_id: UUID, periodo_id: UUID, data: PeriodoContableUpdate
) -> PeriodoContableRead:
    """Actualiza un periodo contable. Lanza NotFoundError si no existe."""
    row = await _update_periodo_contable(
        client_id, periodo_id, data.model_dump(exclude_none=True)
    )
    if not row:
        raise NotFoundError(f"Periodo contable {periodo_id} no encontrado")
    return PeriodoContableRead(**row)
