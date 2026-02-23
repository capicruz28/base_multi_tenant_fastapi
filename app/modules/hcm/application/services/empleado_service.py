"""Servicios de aplicación para hcm_empleado."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.hcm import (
    list_empleados as _list,
    get_empleado_by_id as _get,
    create_empleado as _create,
    update_empleado as _update,
)
from app.modules.hcm.presentation.schemas import EmpleadoCreate, EmpleadoUpdate, EmpleadoRead
from app.core.exceptions import NotFoundError


async def list_empleados(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    estado_empleado: Optional[str] = None,
    es_activo: Optional[bool] = None,
    departamento_id: Optional[UUID] = None,
    cargo_id: Optional[UUID] = None,
    buscar: Optional[str] = None,
) -> List[EmpleadoRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        estado_empleado=estado_empleado,
        es_activo=es_activo,
        departamento_id=departamento_id,
        cargo_id=cargo_id,
        buscar=buscar,
    )
    return [EmpleadoRead(**r) for r in rows]


async def get_empleado_by_id(client_id: UUID, empleado_id: UUID) -> EmpleadoRead:
    row = await _get(client_id, empleado_id)
    if not row:
        raise NotFoundError(f"Empleado {empleado_id} no encontrado")
    return EmpleadoRead(**row)


async def create_empleado(client_id: UUID, data: EmpleadoCreate) -> EmpleadoRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return EmpleadoRead(**row)


async def update_empleado(client_id: UUID, empleado_id: UUID, data: EmpleadoUpdate) -> EmpleadoRead:
    row = await _update(client_id, empleado_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Empleado {empleado_id} no encontrado")
    return EmpleadoRead(**row)
