"""Servicio aplicación cst_producto_costo. Convierte anio <-> año y calcula costo_total/costo_unitario."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from app.infrastructure.database.queries.cst import (
    list_producto_costo as _list,
    get_producto_costo_by_id as _get,
    create_producto_costo as _create,
    update_producto_costo as _update,
)
from app.modules.cst.presentation.schemas import ProductoCostoCreate, ProductoCostoUpdate, ProductoCostoRead
from app.core.exceptions import NotFoundError


def _row_to_read(row: dict) -> dict:
    r = dict(row)
    if "año" in r:
        r["anio"] = r.pop("año")
    md = r.get("costo_material_directo") or Decimal("0")
    mo = r.get("costo_mano_obra_directa") or Decimal("0")
    cif = r.get("costo_indirecto_fabricacion") or Decimal("0")
    r["costo_total"] = md + mo + cif
    qty = r.get("cantidad_producida")
    if qty and qty > 0:
        r["costo_unitario"] = r["costo_total"] / qty
    else:
        r["costo_unitario"] = None
    return r


def _dump_to_db(data: dict) -> dict:
    d = dict(data)
    if "anio" in d:
        d["año"] = d.pop("anio")
    return d


async def list_producto_costo(
    client_id: UUID,
    empresa_id: Optional[UUID] = None,
    producto_id: Optional[UUID] = None,
    anio: Optional[int] = None,
    mes: Optional[int] = None,
    metodo_costeo: Optional[str] = None,
) -> List[ProductoCostoRead]:
    rows = await _list(
        client_id=client_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        anio=anio,
        mes=mes,
        metodo_costeo=metodo_costeo,
    )
    return [ProductoCostoRead(**_row_to_read(r)) for r in rows]


async def get_producto_costo_by_id(client_id: UUID, producto_costo_id: UUID) -> ProductoCostoRead:
    row = await _get(client_id, producto_costo_id)
    if not row:
        raise NotFoundError(f"Producto costo {producto_costo_id} no encontrado")
    return ProductoCostoRead(**_row_to_read(row))


async def create_producto_costo(client_id: UUID, data: ProductoCostoCreate) -> ProductoCostoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _create(client_id, _dump_to_db(dump))
    return ProductoCostoRead(**_row_to_read(row))


async def update_producto_costo(
    client_id: UUID, producto_costo_id: UUID, data: ProductoCostoUpdate
) -> ProductoCostoRead:
    dump = data.model_dump(exclude_none=True)
    row = await _update(client_id, producto_costo_id, dump)
    if not row:
        raise NotFoundError(f"Producto costo {producto_costo_id} no encontrado")
    return ProductoCostoRead(**_row_to_read(row))
