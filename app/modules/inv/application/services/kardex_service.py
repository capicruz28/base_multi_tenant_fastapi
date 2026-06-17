"""
Servicio de Kardex (INV). Consulta de trazabilidad por empresa de sesión.
Aislamiento multi-empresa: empresa_id desde sesión JWT (company_scope).
"""
from __future__ import annotations

from typing import List, Optional, Union
from uuid import UUID
from datetime import date

from app.core.exceptions import NotFoundError
from app.core.tenant.company_scope import require_session_empresa_id
from app.shared.pagination import ErpPaginationParams, ErpSortParams, build_paginated_response
from app.shared.pagination.schemas import ErpPaginatedResponse
from app.infrastructure.database.queries.inv import (
    list_kardex,
    count_kardex,
    get_producto_by_id,
    get_almacen_by_id,
)
from app.modules.inv.presentation.schemas import KardexLineaRead


def _row_to_read(row: dict) -> KardexLineaRead:
    return KardexLineaRead(**row)


async def _validate_optional_filtros_kardex(
    client_id: UUID,
    empresa_id: UUID,
    *,
    producto_id: UUID,
    almacen_id: Optional[UUID] = None,
) -> None:
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


async def list_kardex_servicio(
    client_id: UUID,
    producto_id: UUID,
    almacen_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    pagination: Optional[ErpPaginationParams] = None,
    sort: Optional[ErpSortParams] = None,
) -> Union[List[KardexLineaRead], ErpPaginatedResponse[KardexLineaRead]]:
    """
    Lista líneas de kardex de la empresa activa en sesión.
    producto_id obligatorio. Filtros cross-company → NotFoundError (404).
    """
    empresa_id = require_session_empresa_id()
    await _validate_optional_filtros_kardex(
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
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    list_filtros = {**filtros, "sort_by": sort_by, "sort_dir": sort_dir}
    if pagination is None or not pagination.is_paginated:
        rows = await list_kardex(**list_filtros)
        return [_row_to_read(r) for r in rows]
    total = await count_kardex(**filtros)
    rows = await list_kardex(**list_filtros, pagination=pagination)
    items = [_row_to_read(r) for r in rows]
    return build_paginated_response(items, total, pagination)
