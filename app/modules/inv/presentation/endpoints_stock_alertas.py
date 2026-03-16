"""Endpoints INV - Alertas de stock."""
from fastapi import APIRouter, Depends, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import StockRead
from app.infrastructure.database.queries.inv import list_stock_alertas_bajo_minimo

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "stock"


@router.get(
    "",
    response_model=list[StockRead],
    summary="Alertas: stock bajo mínimo (por disponible)",
)
async def alertas_stock_bajo_minimo(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    almacen_id: Optional[UUID] = Query(None, description="Filtrar por almacén"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    client_id = current_user.cliente_id
    rows = await list_stock_alertas_bajo_minimo(
        client_id=client_id,
        empresa_id=empresa_id,
        almacen_id=almacen_id,
    )
    return [StockRead(**r) for r in rows]

