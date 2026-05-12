"""Servicio aplicación mfg_lista_materiales (BOM)."""
from typing import List, Optional
from uuid import UUID
from app.modules.org.application.services.empresa_service import get_empresa_servicio
from app.infrastructure.database.queries.mfg import (
    list_listas_materiales as _list,
    get_lista_materiales_by_id as _get,
    create_lista_materiales as _create,
    update_lista_materiales as _update,
)
from app.modules.mfg.presentation.schemas import ListaMaterialesCreate, ListaMaterialesUpdate, ListaMaterialesRead
from app.core.exceptions import NotFoundError, ServiceError

_ESTADO_BOM_BORRADOR = "borrador"
_ESTADO_BOM_APROBADA = "aprobada"
_ESTADO_BOM_OBSOLETA = "obsoleta"

_BOM_EDITABLE_STATES = {_ESTADO_BOM_BORRADOR}


def _assert_bom_editable(estado: Optional[str]) -> None:
    if (estado or "").strip().lower() not in _BOM_EDITABLE_STATES:
        raise ServiceError(
            status_code=409,
            detail=f"No se permite editar la BOM en estado '{estado}'. Solo se permite en: {sorted(_BOM_EDITABLE_STATES)}",
            internal_code="MFG_BOM_NOT_EDITABLE",
        )


def _assert_transition(current: str, allowed_from: set[str], action: str) -> None:
    if current not in allowed_from:
        raise ServiceError(
            status_code=409,
            detail=f"No se puede '{action}' una BOM desde estado '{current}'. Estados permitidos: {sorted(allowed_from)}",
            internal_code="MFG_BOM_INVALID_TRANSITION",
        )

async def list_listas_materiales(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    es_bom_activa: Optional[bool] = None,
    estado: Optional[str] = None,
    buscar: Optional[str] = None,
) -> List[ListaMaterialesRead]:
    if empresa_id is not None:
        await get_empresa_servicio(client_id=client_id, empresa_id=empresa_id)
    rows = await _list(client_id=client_id, empresa_id=empresa_id, producto_id=producto_id, es_bom_activa=es_bom_activa, estado=estado, buscar=buscar)
    return [ListaMaterialesRead(**r) for r in rows]

async def get_lista_materiales_by_id(client_id: UUID, bom_id: UUID) -> ListaMaterialesRead:
    row = await _get(client_id, bom_id)
    if not row:
        raise NotFoundError(f"Lista de materiales (BOM) {bom_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=row["empresa_id"])
    return ListaMaterialesRead(**row)

async def create_lista_materiales(client_id: UUID, data: ListaMaterialesCreate) -> ListaMaterialesRead:
    await get_empresa_servicio(client_id=client_id, empresa_id=data.empresa_id)
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return ListaMaterialesRead(**row)

async def update_lista_materiales(client_id: UUID, bom_id: UUID, data: ListaMaterialesUpdate) -> ListaMaterialesRead:
    current = await _get(client_id, bom_id)
    if not current:
        raise NotFoundError(f"Lista de materiales (BOM) {bom_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=current["empresa_id"])
    _assert_bom_editable(current.get("estado"))

    payload = data.model_dump(exclude_none=True)
    payload.pop("estado", None)  # estado se cambia solo por transiciones explícitas
    payload.pop("aprobado_por_usuario_id", None)
    payload.pop("fecha_aprobacion", None)

    row = await _update(client_id, bom_id, payload)
    if not row:
        raise NotFoundError(f"Lista de materiales (BOM) {bom_id} no encontrada")
    return ListaMaterialesRead(**row)


async def aprobar_lista_materiales(client_id: UUID, bom_id: UUID, aprobado_por_usuario_id: Optional[UUID] = None) -> ListaMaterialesRead:
    current = await _get(client_id, bom_id)
    if not current:
        raise NotFoundError(f"Lista de materiales (BOM) {bom_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=current["empresa_id"])
    estado_actual = (current.get("estado") or "").strip().lower()
    _assert_transition(estado_actual, {_ESTADO_BOM_BORRADOR}, "aprobar")

    row = await _update(
        client_id,
        bom_id,
        {
            "estado": _ESTADO_BOM_APROBADA,
            "aprobado_por_usuario_id": aprobado_por_usuario_id,
        },
    )
    if not row:
        raise NotFoundError(f"Lista de materiales (BOM) {bom_id} no encontrada")
    return ListaMaterialesRead(**row)


async def anular_lista_materiales(client_id: UUID, bom_id: UUID) -> ListaMaterialesRead:
    current = await _get(client_id, bom_id)
    if not current:
        raise NotFoundError(f"Lista de materiales (BOM) {bom_id} no encontrada")
    await get_empresa_servicio(client_id=client_id, empresa_id=current["empresa_id"])
    estado_actual = (current.get("estado") or "").strip().lower()
    _assert_transition(estado_actual, {_ESTADO_BOM_BORRADOR, _ESTADO_BOM_APROBADA}, "anular")

    row = await _update(client_id, bom_id, {"estado": _ESTADO_BOM_OBSOLETA, "es_bom_activa": False})
    if not row:
        raise NotFoundError(f"Lista de materiales (BOM) {bom_id} no encontrada")
    return ListaMaterialesRead(**row)
