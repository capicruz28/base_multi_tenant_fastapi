"""Servicio aplicación mrp_explosion_materiales."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from app.infrastructure.database.queries.mrp import (
    list_explosion_materiales as _list,
    get_explosion_materiales_by_id as _get,
    create_explosion_materiales as _create,
    update_explosion_materiales as _update,
)
from app.modules.mrp.presentation.schemas import (
    ExplosionMaterialesCreate,
    ExplosionMaterialesUpdate,
    ExplosionMaterialesRead,
)
from app.core.exceptions import NotFoundError


def _enrich_explosion_row(row: dict) -> dict:
    """Añade stock_disponible y cantidad_a_ordenar calculados."""
    sa = row.get("stock_actual") or Decimal("0")
    sr = row.get("stock_reservado") or Decimal("0")
    st = row.get("stock_transito") or Decimal("0")
    cn = row.get("cantidad_necesaria") or Decimal("0")
    stock_disp = sa - sr + st
    row["stock_disponible"] = stock_disp
    row["cantidad_a_ordenar"] = max(Decimal("0"), cn - stock_disp)
    return row


async def list_explosion_materiales(
    client_id: UUID,
    plan_maestro_id: Optional[UUID] = None,
    producto_componente_id: Optional[UUID] = None,
    nivel_bom: Optional[int] = None,
) -> List[ExplosionMaterialesRead]:
    rows = await _list(
        client_id=client_id,
        plan_maestro_id=plan_maestro_id,
        producto_componente_id=producto_componente_id,
        nivel_bom=nivel_bom,
    )
    return [ExplosionMaterialesRead(**_enrich_explosion_row(dict(r))) for r in rows]


async def get_explosion_materiales_by_id(client_id: UUID, explosion_id: UUID) -> ExplosionMaterialesRead:
    row = await _get(client_id, explosion_id)
    if not row:
        raise NotFoundError(f"Explosión materiales {explosion_id} no encontrada")
    return ExplosionMaterialesRead(**_enrich_explosion_row(dict(row)))


async def create_explosion_materiales(client_id: UUID, data: ExplosionMaterialesCreate) -> ExplosionMaterialesRead:
    row = await _create(client_id, data.model_dump(exclude_none=True))
    return ExplosionMaterialesRead(**_enrich_explosion_row(dict(row)))


async def update_explosion_materiales(
    client_id: UUID, explosion_id: UUID, data: ExplosionMaterialesUpdate
) -> ExplosionMaterialesRead:
    row = await _update(client_id, explosion_id, data.model_dump(exclude_none=True))
    if not row:
        raise NotFoundError(f"Explosión materiales {explosion_id} no encontrada")
    return ExplosionMaterialesRead(**_enrich_explosion_row(dict(row)))
