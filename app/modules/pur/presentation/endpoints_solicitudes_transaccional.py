# app/modules/pur/presentation/endpoints_solicitudes_transaccional.py
"""
Endpoints PUR - Solicitudes (cabecera + detalle transaccional).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.core.exceptions import NotFoundError
from app.modules.pur.application.services.pur_transaccional_creacion_service import (
    create_solicitud_transaccional_servicio,
)
from app.modules.pur.presentation.schemas import (
    SolicitudCompraRead,
    SolicitudCompraTransaccionalCreate,
)
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

MODULE_CODE = "pur"
RESOURCE_CODE = "solicitud"

router = APIRouter()


@router.post(
    "/transaccional",
    response_model=SolicitudCompraRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear solicitud de compra (cabecera+detalle) transaccional",
)
async def crear_solicitud_transaccional(
    data: SolicitudCompraTransaccionalCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    client_id = current_user.cliente_id
    try:
        return await create_solicitud_transaccional_servicio(client_id=client_id, data=data)
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

