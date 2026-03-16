# app/modules/org/application/services/cargo_service.py
"""Servicio de Cargo (ORG). client_id desde contexto."""
from typing import List, Optional
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.infrastructure.database.queries.org import (
    list_cargos,
    get_cargo_by_id,
    create_cargo,
    update_cargo,
)
from app.modules.org.presentation.schemas import (
    CargoCreate,
    CargoUpdate,
    CargoRead,
)


def _row_to_read(row: dict) -> CargoRead:
    return CargoRead(**row)


async def list_cargos_servicio(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
) -> List[CargoRead]:
    rows = await list_cargos(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
    )
    cargos = [_row_to_read(r) for r in rows]
    if buscar:
        term = buscar.lower()
        cargos = [
            c
            for c in cargos
            if term in (c.codigo or "").lower() or term in (c.nombre or "").lower()
        ]
    return cargos


async def get_cargo_servicio(
    client_id: UUID,
    cargo_id: UUID,
) -> CargoRead:
    row = await get_cargo_by_id(client_id=client_id, cargo_id=cargo_id)
    if not row:
        raise NotFoundError(detail="Cargo no encontrado")
    return _row_to_read(row)


async def create_cargo_servicio(
    client_id: UUID,
    data: CargoCreate,
) -> CargoRead:
    payload = data.model_dump()
    row = await create_cargo(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_cargo_servicio(
    client_id: UUID,
    cargo_id: UUID,
    data: CargoUpdate,
) -> CargoRead:
    row = await get_cargo_by_id(client_id=client_id, cargo_id=cargo_id)
    if not row:
        raise NotFoundError(detail="Cargo no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_cargo(
        client_id=client_id,
        cargo_id=cargo_id,
        data=payload,
    )
    return _row_to_read(updated)


async def delete_cargo_servicio(
    client_id: UUID,
    cargo_id: UUID,
) -> None:
    """
    Baja lógica de un cargo (es_activo = False).
    """
    row = await get_cargo_by_id(client_id=client_id, cargo_id=cargo_id)
    if not row:
        raise NotFoundError(detail="Cargo no encontrado")
    await update_cargo(
        client_id=client_id,
        cargo_id=cargo_id,
        data={"es_activo": False},
    )
