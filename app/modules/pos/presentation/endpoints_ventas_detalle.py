"""
Endpoints FastAPI para pos_venta_detalle.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pos.application.services import (
    list_venta_detalles,
    get_venta_detalle_by_id,
    create_venta_detalle,
    update_venta_detalle,
)
from app.modules.pos.presentation.schemas import (
    VentaDetalleCreate,
    VentaDetalleUpdate,
    VentaDetalleRead,
)
from app.core.exceptions import NotFoundError, ValidationError

MODULE_CODE = "pos"
RESOURCE_CODE = "venta_detalle"

router = APIRouter()


@router.get("", response_model=List[VentaDetalleRead], tags=["POS - Detalle de Ventas"])
async def get_venta_detalles(
    empresa_id: Optional[UUID] = Query(None),
    venta_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista detalles de venta POS. Opcionalmente filtra por venta_id y empresa_id."""
    return await list_venta_detalles(
        client_id=current_user.cliente_id,
        venta_id=venta_id,
        empresa_id=empresa_id,
    )


@router.get("/{venta_detalle_id}", response_model=VentaDetalleRead, tags=["POS - Detalle de Ventas"])
async def get_venta_detalle(
    venta_detalle_id: UUID,
    empresa_id: Optional[UUID] = Query(
        None,
        description="Si se informa, la fila debe pertenecer a esta empresa.",
    ),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Obtiene un detalle de venta por id."""
    try:
        return await get_venta_detalle_by_id(
            current_user.cliente_id,
            venta_detalle_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=VentaDetalleRead, status_code=status.HTTP_201_CREATED, tags=["POS - Detalle de Ventas"])
async def post_venta_detalle(
    data: VentaDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea un detalle de venta (línea de item)."""
    try:
        return await create_venta_detalle(current_user.cliente_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.put("/{venta_detalle_id}", response_model=VentaDetalleRead, tags=["POS - Detalle de Ventas"])
async def put_venta_detalle(
    venta_detalle_id: UUID,
    data: VentaDetalleUpdate,
    empresa_id: Optional[UUID] = Query(
        None,
        description="Si se informa, la fila debe pertenecer a esta empresa.",
    ),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza un detalle de venta."""
    try:
        return await update_venta_detalle(
            current_user.cliente_id,
            venta_detalle_id,
            data,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
