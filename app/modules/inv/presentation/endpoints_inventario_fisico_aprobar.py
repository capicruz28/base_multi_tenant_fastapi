"""Endpoints INV - Aprobación de inventario físico."""
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.inv.presentation.schemas import InventarioFisicoRead
from app.modules.inv.presentation.schemas_proceso import AprobarInventarioFisicoRequest
from app.modules.inv.application.services import inventario_fisico_aprobacion_service
from app.core.exceptions import NotFoundError

router = APIRouter()

MODULE_CODE = "inv"
RESOURCE_CODE = "inventario_fisico"


@router.post(
    "/{inventario_fisico_id}/aprobar",
    response_model=InventarioFisicoRead,
    summary="Aprobar inventario físico (genera ajuste y actualiza stock)",
)
async def aprobar_inventario_fisico(
    inventario_fisico_id: UUID,
    data: AprobarInventarioFisicoRequest,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(
        require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")
    ),
):
    client_id = current_user.cliente_id
    try:
        return await inventario_fisico_aprobacion_service.aprobar_inventario_fisico_servicio(
            client_id=client_id,
            inventario_fisico_id=inventario_fisico_id,
            tipo_movimiento_id=data.tipo_movimiento_id,
            usuario_id=current_user.usuario_id,
            observaciones=data.observaciones,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

