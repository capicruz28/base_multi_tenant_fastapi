# app/modules/inv/application/services/producto_service.py
"""
Servicio de Producto (INV). client_id siempre desde contexto, nunca desde body.
Aislamiento multi-empresa: empresa_id desde sesión JWT (company_scope).
"""
from typing import List, Optional, Union
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.core.tenant.company_scope import (
    require_session_empresa_id,
    enforce_body_empresa_matches_session,
    ensure_empresa_in_tenant,
)
from app.shared.pagination import ErpPaginationParams, ErpSortParams, build_paginated_response
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.infrastructure.database.queries.inv import (
    list_productos,
    count_productos,
    get_producto_by_id,
    get_producto_by_sku,
    create_producto,
    update_producto,
    get_categoria_by_id,
    get_unidad_medida_by_id,
)
from app.modules.inv.application.services.inv_audit_context import (
    apply_create_audit,
    apply_producto_update_audit,
)
from app.modules.inv.presentation.schemas import (
    ProductoCreate,
    ProductoUpdate,
    ProductoRead,
)


def _row_to_read(row: dict) -> ProductoRead:
    return ProductoRead(**row)


async def _validate_producto_referencias_empresa(
    client_id: UUID,
    empresa_id: UUID,
    *,
    categoria_id: Optional[UUID] = None,
    subcategoria_id: Optional[UUID] = None,
    unidad_medida_base_id: Optional[UUID] = None,
    unidad_medida_compra_id: Optional[UUID] = None,
    unidad_medida_venta_id: Optional[UUID] = None,
) -> None:
    """Referencias de catálogo deben existir en la misma empresa activa."""
    if categoria_id is not None:
        cat = await get_categoria_by_id(
            client_id=client_id,
            categoria_id=categoria_id,
            empresa_id=empresa_id,
        )
        if not cat:
            raise NotFoundError(detail="Categoría no encontrada")
    if subcategoria_id is not None:
        sub = await get_categoria_by_id(
            client_id=client_id,
            categoria_id=subcategoria_id,
            empresa_id=empresa_id,
        )
        if not sub:
            raise NotFoundError(detail="Subcategoría no encontrada")
    for um_id, label in (
        (unidad_medida_base_id, "Unidad de medida base"),
        (unidad_medida_compra_id, "Unidad de medida de compra"),
        (unidad_medida_venta_id, "Unidad de medida de venta"),
    ):
        if um_id is not None:
            um = await get_unidad_medida_by_id(
                client_id=client_id,
                unidad_medida_id=um_id,
                empresa_id=empresa_id,
            )
            if not um:
                raise NotFoundError(detail=f"{label} no encontrada")


async def list_productos_servicio(
    client_id: UUID,
    categoria_id: Optional[UUID] = None,
    tipo_producto: Optional[str] = None,
    solo_activos: bool = True,
    buscar: Optional[str] = None,
    pagination: Optional[ErpPaginationParams] = None,
    sort: Optional[ErpSortParams] = None,
) -> Union[List[ProductoRead], ErpPaginatedResponse[ProductoRead]]:
    empresa_id = require_session_empresa_id()
    sort_by = sort.sort_by if sort else None
    sort_dir = sort.sort_dir if sort and sort.is_active else None
    filtros = dict(
        client_id=client_id,
        empresa_id=empresa_id,
        categoria_id=categoria_id,
        tipo_producto=tipo_producto,
        solo_activos=solo_activos,
        buscar=buscar,
    )
    list_filtros = {**filtros, "sort_by": sort_by, "sort_dir": sort_dir}
    if pagination is None or not pagination.is_paginated:
        rows = await list_productos(**list_filtros)
        return [_row_to_read(r) for r in rows]
    total = await count_productos(**filtros)
    rows = await list_productos(**list_filtros, pagination=pagination)
    items = [_row_to_read(r) for r in rows]
    return build_paginated_response(items, total, pagination)


async def get_producto_servicio(
    client_id: UUID,
    producto_id: UUID,
) -> ProductoRead:
    empresa_id = require_session_empresa_id()
    row = await get_producto_by_id(
        client_id=client_id,
        producto_id=producto_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Producto no encontrado")
    return _row_to_read(row)


async def create_producto_servicio(
    client_id: UUID,
    data: ProductoCreate,
    usuario_id: Optional[UUID] = None,
) -> ProductoRead:
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    await _validate_producto_referencias_empresa(
        client_id,
        empresa_id,
        categoria_id=data.categoria_id,
        subcategoria_id=data.subcategoria_id,
        unidad_medida_base_id=data.unidad_medida_base_id,
        unidad_medida_compra_id=data.unidad_medida_compra_id,
        unidad_medida_venta_id=data.unidad_medida_venta_id,
    )
    existing = await get_producto_by_sku(
        client_id=client_id,
        empresa_id=empresa_id,
        codigo_sku=data.codigo_sku,
    )
    if existing:
        from app.core.exceptions import ConflictError

        raise ConflictError(
            detail=f"Ya existe un producto con SKU '{data.codigo_sku}' en esta empresa.",
        )
    payload = data.model_dump()
    payload["empresa_id"] = empresa_id
    payload = apply_create_audit(payload, usuario_id)
    row = await create_producto(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_producto_servicio(
    client_id: UUID,
    producto_id: UUID,
    data: ProductoUpdate,
    usuario_id: Optional[UUID] = None,
) -> ProductoRead:
    empresa_id = require_session_empresa_id()
    row = await get_producto_by_id(
        client_id=client_id,
        producto_id=producto_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Producto no encontrado")
    payload = data.model_dump(exclude_unset=True)
    if "codigo_sku" in payload and payload["codigo_sku"] != row.get("codigo_sku"):
        dup = await get_producto_by_sku(
            client_id=client_id,
            empresa_id=empresa_id,
            codigo_sku=payload["codigo_sku"],
        )
        if dup and dup.get("producto_id") != producto_id:
            from app.core.exceptions import ConflictError

            raise ConflictError(
                detail=f"Ya existe un producto con SKU '{payload['codigo_sku']}' en esta empresa.",
            )
    await _validate_producto_referencias_empresa(
        client_id,
        empresa_id,
        categoria_id=payload.get("categoria_id"),
        subcategoria_id=payload.get("subcategoria_id"),
        unidad_medida_base_id=payload.get("unidad_medida_base_id"),
        unidad_medida_compra_id=payload.get("unidad_medida_compra_id"),
        unidad_medida_venta_id=payload.get("unidad_medida_venta_id"),
    )
    payload = apply_producto_update_audit(payload, usuario_id)
    updated = await update_producto(
        client_id=client_id,
        producto_id=producto_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)
