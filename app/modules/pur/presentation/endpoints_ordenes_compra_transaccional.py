# app/modules/pur/presentation/endpoints_ordenes_compra_transaccional.py
"""
Endpoints PUR - Órdenes de Compra (cabecera + detalle transaccional).
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.core.exceptions import NotFoundError
from app.modules.pur.application.services.pur_transaccional_creacion_service import (
    create_orden_compra_transaccional_servicio,
)
from app.modules.pur.presentation.schemas import (
    OrdenCompraRead,
    OrdenCompraTransaccionalCreate,
)
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

MODULE_CODE = "pur"
RESOURCE_CODE = "orden_compra"

router = APIRouter()


@router.post(
    "/transaccional",
    response_model=OrdenCompraRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear orden de compra (cabecera+detalle) transaccional",
)
async def crear_orden_compra_transaccional(
    data: OrdenCompraTransaccionalCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    client_id = current_user.cliente_id
    try:
        return await create_orden_compra_transaccional_servicio(client_id=client_id, data=data)
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

