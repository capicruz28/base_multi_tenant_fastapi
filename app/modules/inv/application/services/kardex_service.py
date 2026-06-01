"""
Servicio de Kardex (INV). Consulta de trazabilidad por empresa de sesión.
Aislamiento multi-empresa: empresa_id desde sesión JWT (company_scope).
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID
from datetime import date

from app.core.exceptions import NotFoundError
from app.core.tenant.company_scope import require_session_empresa_id
from app.infrastructure.database.queries.inv import (
    list_kardex,
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


async def list_kardex_servicio(
    client_id: UUID,
    producto_id: Optional[UUID] = None,
    almacen_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> List[KardexLineaRead]:
    """
    Lista líneas de kardex de la empresa activa en sesión.
    Filtros producto/almacén cross-company → NotFoundError (404).
    """
    empresa_id = require_session_empresa_id()
    await _validate_optional_filtros_kardex(
        client_id,
        empresa_id,
        producto_id=producto_id,
        almacen_id=almacen_id,
    )
    rows = await list_kardex(
        client_id=client_id,
        empresa_id=empresa_id,
        producto_id=producto_id,
        almacen_id=almacen_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return [_row_to_read(r) for r in rows]
