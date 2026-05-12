"""
Endpoints FastAPI para pos_venta.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pos.application.services import (
    list_ventas,
    get_venta_by_id,
    create_venta,
    update_venta,
    anular_venta,
)
from app.modules.pos.presentation.schemas import (
    VentaCreate,
    VentaUpdate,
    VentaRead,
    VentaAnularRequest,
)
from app.core.exceptions import NotFoundError, ValidationError

MODULE_CODE = "pos"
RESOURCE_CODE = "venta"

router = APIRouter()


def _http_val_err(e: ValidationError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("", response_model=List[VentaRead], tags=["POS - Ventas"])
async def get_ventas(
    empresa_id: Optional[UUID] = Query(None),
    punto_venta_id: Optional[UUID] = Query(None),
    turno_caja_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista ventas POS del tenant."""
    return await list_ventas(
        client_id=current_user.cliente_id,
        punto_venta_id=punto_venta_id,
        turno_caja_id=turno_caja_id,
        empresa_id=empresa_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.post(
    "/{venta_id}/anular",
    response_model=VentaRead,
    tags=["POS - Ventas"],
    summary="Anular venta POS",
)
async def post_anular_venta(
    venta_id: UUID,
    data: VentaAnularRequest,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.anular")),
):
    try:
        return await anular_venta(
            current_user.cliente_id,
            venta_id,
            data,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise _http_val_err(e)


@router.get("/{venta_id}", response_model=VentaRead, tags=["POS - Ventas"])
async def get_venta(
    venta_id: UUID,
    empresa_id: Optional[UUID] = Query(
        None,
        description="Si se informa, la fila debe pertenecer a esta empresa.",
    ),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Obtiene una venta POS por id."""
    try:
        return await get_venta_by_id(
            current_user.cliente_id,
            venta_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=VentaRead, status_code=status.HTTP_201_CREATED, tags=["POS - Ventas"])
async def post_venta(
    data: VentaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una venta POS."""
    return await create_venta(current_user.cliente_id, data)


@router.put("/{venta_id}", response_model=VentaRead, tags=["POS - Ventas"])
async def put_venta(
    venta_id: UUID,
    data: VentaUpdate,
    empresa_id: Optional[UUID] = Query(
        None,
        description="Si se informa, la fila debe pertenecer a esta empresa.",
    ),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una venta POS (solo borrador/pendiente)."""
    try:
        return await update_venta(
            current_user.cliente_id,
            venta_id,
            data,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise _http_val_err(e)
