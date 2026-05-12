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
from app.infrastructure.database.queries.fin.periodo_contable_queries import (
    count_asientos_borrador_en_periodo as _count_asientos_borrador_en_periodo,
    cerrar_periodo_contable as _cerrar_periodo_contable_query,
)
from app.modules.fin.presentation.schemas import (
    PeriodoContableCreate,
    PeriodoContableUpdate,
    PeriodoContableRead,
)
from app.core.exceptions import NotFoundError, ServiceError


def _estado_periodo_norm(value: Optional[str]) -> str:
    return (value or "").strip().lower()


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


async def cerrar_periodo_contable(
    client_id: UUID, periodo_id: UUID, cerrado_por_usuario_id: UUID
) -> PeriodoContableRead:
    """
    Cierra el periodo. Exige que no existan asientos en borrador para ese periodo.
    """
    current = await _get_periodo_contable_by_id(client_id, periodo_id)
    if not current:
        raise NotFoundError(f"Periodo contable {periodo_id} no encontrado")
    est = _estado_periodo_norm(current.get("estado"))
    if est in ("cerrado", "bloqueado"):
        raise ServiceError(
            status_code=409,
            detail="El periodo ya está cerrado o bloqueado.",
            internal_code="FIN_PERIODO_YA_CERRADO",
        )
    n_borrador = await _count_asientos_borrador_en_periodo(client_id, periodo_id)
    if n_borrador > 0:
        raise ServiceError(
            status_code=400,
            detail=f"Existen {n_borrador} asiento(s) en borrador; no se puede cerrar el periodo.",
            internal_code="FIN_PERIODO_ASIENTOS_BORRADOR",
        )
    row = await _cerrar_periodo_contable_query(
        client_id, periodo_id, cerrado_por_usuario_id
    )
    if not row:
        raise NotFoundError(f"Periodo contable {periodo_id} no encontrado")
    return PeriodoContableRead(**row)
