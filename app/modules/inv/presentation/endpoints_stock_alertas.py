"""Endpoints INV - Alertas de stock."""
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.modules.inv.presentation.inv_deps import get_inv_session_client_id
from app.core.authorization.rbac import require_permission
from app.core.exceptions import NotFoundError
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import StockRead
from app.modules.inv.application.services import stock_service

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "stock"


@router.get(
    "",
    response_model=list[StockRead],
    summary="Alertas: stock bajo mínimo (por disponible)",
)
async def alertas_stock_bajo_minimo(
    almacen_id: Optional[UUID] = Query(None, description="Filtrar por almacén"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
    client_id: UUID = Depends(get_inv_session_client_id),
):
    """Alertas de stock bajo mínimo para la empresa activa en sesión."""
    try:
        return await stock_service.list_stock_alertas_servicio(
            client_id=client_id,
            almacen_id=almacen_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
