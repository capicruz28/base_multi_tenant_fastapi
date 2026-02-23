"""Servicios de aplicación para hcm_concepto_planilla."""
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.hcm import (
    list_conceptos_planilla as _list,
    get_concepto_planilla_by_id as _get,
    create_concepto_planilla as _create,
    update_concepto_planilla as _update,
)
from app.modules.hcm.presentation.schemas import ConceptoPlanillaCreate, ConceptoPlanillaUpdate, ConceptoPlanillaRead
from app.core.exceptions import NotFoundError


async def list_conceptos_planilla(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    tipo_concepto: Optional[str] = None,
    es_activo: Optional[bool] = None,
    buscar: Optional[str] = None,
) -> List[ConceptoPlanillaRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        tipo_concepto=tipo_concepto,
        es_activo=es_activo,
        buscar=buscar,
    )
    return [ConceptoPlanillaRead(**r) for r in rows]


async def get_concepto_planilla_by_id(client_id: UUID, concepto_id: UUID) -> ConceptoPlanillaRead:
    row = await _get(client_id, concepto_id)
    if not row:
        raise NotFoundError(f"Concepto de planilla {concepto_id} no encontrado")
    return ConceptoPlanillaRead(**row)


async def create_concepto_planilla(client_id: UUID, data: ConceptoPlanillaCreate) -> ConceptoPlanillaRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return ConceptoPlanillaRead(**row)


async def update_concepto_planilla(
    client_id: UUID, concepto_id: UUID, data: ConceptoPlanillaUpdate
) -> ConceptoPlanillaRead:
    row = await _update(client_id, concepto_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Concepto de planilla {concepto_id} no encontrado")
    return ConceptoPlanillaRead(**row)
