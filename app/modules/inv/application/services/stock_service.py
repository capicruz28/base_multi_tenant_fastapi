# app/modules/inv/application/services/stock_service.py
"""
Servicio de Stock (INV). client_id siempre desde contexto, nunca desde body.
Aislamiento multi-empresa: empresa_id desde sesión JWT (company_scope).
"""
from typing import List, Optional, Union
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.inv.application.services.inv_stock_write_policy import (
    assert_stock_direct_write_allowed,
)
from app.core.tenant.company_scope import (
    require_session_empresa_id,
    enforce_body_empresa_matches_session,
    ensure_empresa_in_tenant,
)
from app.core.tenant.empresa_context import coerce_empresa_id
from app.shared.pagination import ErpPaginationParams, ErpSortParams, build_paginated_response
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.infrastructure.database.queries.inv import (
    list_stocks,
    count_stocks,
    get_stock_by_id,
    get_stock_by_producto_almacen,
    create_stock,
    update_stock,
    list_stock_alertas_bajo_minimo,
    count_stock_alertas_bajo_minimo,
    get_producto_by_id,
    get_almacen_by_id,
)
from app.modules.inv.presentation.schemas import (
    StockCreate,
    StockUpdate,
    StockRead,
)


def _row_to_read(row: dict) -> StockRead:
    return StockRead(**row)


async def _validate_producto_almacen_empresa(
    client_id: UUID,
    empresa_id: UUID,
    producto_id: UUID,
    almacen_id: UUID,
) -> None:
    """
    Producto y almacén deben existir y pertenecer a la empresa de sesión.
    Cross-company o referencias cruzadas → NotFoundError (404).
    """
    producto = await get_producto_by_id(
        client_id=client_id,
        producto_id=producto_id,
        empresa_id=empresa_id,
    )
    if not producto:
        raise NotFoundError(detail="Producto no encontrado")

    almacen = await get_almacen_by_id(
        client_id=client_id,
        almacen_id=almacen_id,
        empresa_id=empresa_id,
    )
    if not almacen:
        raise NotFoundError(detail="Almacén no encontrado")

    prod_emp = coerce_empresa_id(producto.get("empresa_id"))
    alm_emp = coerce_empresa_id(almacen.get("empresa_id"))
    if prod_emp != alm_emp or prod_emp != empresa_id:
        raise ValidationError(
            detail="Producto y almacén deben pertenecer a la misma empresa activa de la sesión.",
            internal_code="STOCK_EMPRESA_MISMATCH",
        )


async def _validate_optional_filtro_empresa(
    client_id: UUID,
    empresa_id: UUID,
    *,
    producto_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
) -> None:
    if producto_id is not None:
        prod = await get_producto_by_id(
            client_id=client_id,
            producto_id=producto_id,
            empresa_id=empresa_id,
        )
        if not prod:
            raise NotFoundError(detail="Producto no encontrado")
    if almacen_id is not None:
        alm = await get_almacen_by_id(
            client_id=client_id,
            almacen_id=almacen_id,
            empresa_id=empresa_id,
        )
        if not alm:
            raise NotFoundError(detail="Almacén no encontrado")


async def list_stocks_servicio(
    client_id: UUID,
    producto_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    pagination: Optional[ErpPaginationParams] = None,
    sort: Optional[ErpSortParams] = None,
) -> Union[List[StockRead], ErpPaginatedResponse[StockRead]]:
    empresa_id = require_session_empresa_id()
    await _validate_optional_filtro_empresa(
        client_id,
        empresa_id,
        producto_id=producto_id,
        almacen_id=almacen_id,
    )
    sort_by = sort.sort_by if sort else None
    sort_dir = sort.sort_dir if sort and sort.is_active else None
    filtros = dict(
        client_id=client_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        almacen_id=almacen_id,
    )
    list_filtros = {**filtros, "sort_by": sort_by, "sort_dir": sort_dir}
    if pagination is None or not pagination.is_paginated:
        rows = await list_stocks(**list_filtros)
        return [_row_to_read(r) for r in rows]
    total = await count_stocks(**filtros)
    rows = await list_stocks(**list_filtros, pagination=pagination)
    items = [_row_to_read(r) for r in rows]
    return build_paginated_response(items, total, pagination)


async def get_stock_servicio(
    client_id: UUID,
    stock_id: UUID,
) -> StockRead:
    empresa_id = require_session_empresa_id()
    row = await get_stock_by_id(
        client_id=client_id,
        stock_id=stock_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Stock no encontrado")
    return _row_to_read(row)


async def get_stock_by_producto_almacen_servicio(
    client_id: UUID,
    producto_id: UUID,
    almacen_id: UUID,
) -> Optional[StockRead]:
    empresa_id = require_session_empresa_id()
    await _validate_producto_almacen_empresa(
        client_id, empresa_id, producto_id, almacen_id
    )
    row = await get_stock_by_producto_almacen(
        client_id=client_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        almacen_id=almacen_id,
    )
    return _row_to_read(row) if row else None


async def list_stock_alertas_servicio(
    client_id: UUID,
    almacen_id: Optional[UUID] = None,
    pagination: Optional[ErpPaginationParams] = None,
    sort: Optional[ErpSortParams] = None,
) -> Union[List[StockRead], ErpPaginatedResponse[StockRead]]:
    empresa_id = require_session_empresa_id()
    if almacen_id is not None:
        await _validate_optional_filtro_empresa(
            client_id, empresa_id, almacen_id=almacen_id
        )
    sort_by = sort.sort_by if sort else None
    sort_dir = sort.sort_dir if sort and sort.is_active else None
    filtros = dict(client_id=client_id, empresa_id=empresa_id, almacen_id=almacen_id)
    list_filtros = {**filtros, "sort_by": sort_by, "sort_dir": sort_dir}
    if pagination is None or not pagination.is_paginated:
        rows = await list_stock_alertas_bajo_minimo(**list_filtros)
        return [_row_to_read(r) for r in rows]
    total = await count_stock_alertas_bajo_minimo(**filtros)
    rows = await list_stock_alertas_bajo_minimo(**list_filtros, pagination=pagination)
    items = [_row_to_read(r) for r in rows]
    return build_paginated_response(items, total, pagination)


async def create_stock_servicio(
    client_id: UUID,
    data: StockCreate,
) -> StockRead:
    assert_stock_direct_write_allowed()
    empresa_id = enforce_body_empresa_matches_session(data.empresa_id)
    await ensure_empresa_in_tenant(client_id=client_id, empresa_id=empresa_id)
    await _validate_producto_almacen_empresa(
        client_id, empresa_id, data.producto_id, data.almacen_id
    )
    payload = data.model_dump()
    payload["empresa_id"] = empresa_id
    row = await create_stock(client_id=client_id, data=payload)
    return _row_to_read(row)


async def update_stock_servicio(
    client_id: UUID,
    stock_id: UUID,
    data: StockUpdate,
) -> StockRead:
    assert_stock_direct_write_allowed()
    empresa_id = require_session_empresa_id()
    row = await get_stock_by_id(
        client_id=client_id,
        stock_id=stock_id,
        empresa_id=empresa_id,
    )
    if not row:
        raise NotFoundError(detail="Stock no encontrado")
    payload = data.model_dump(exclude_unset=True)
    updated = await update_stock(
        client_id=client_id,
        stock_id=stock_id,
        data=payload,
        empresa_id=empresa_id,
    )
    return _row_to_read(updated)
