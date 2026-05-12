"""
Endpoints FastAPI para pos_turno_caja.
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
    list_turnos_caja,
    get_turno_caja_by_id,
    create_turno_caja,
    update_turno_caja,
    cerrar_turno_caja,
)
from app.modules.pos.presentation.schemas import (
    TurnoCajaCreate,
    TurnoCajaUpdate,
    TurnoCajaRead,
    TurnoCajaCerrarRequest,
)
from app.core.exceptions import NotFoundError, ValidationError

MODULE_CODE = "pos"
RESOURCE_CODE = "turno_caja"

router = APIRouter()


@router.get("", response_model=List[TurnoCajaRead], tags=["POS - Turnos de Caja"])
async def get_turnos_caja(
    empresa_id: Optional[UUID] = Query(None),
    punto_venta_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    cajero_usuario_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista turnos de caja del tenant."""
    return await list_turnos_caja(
        client_id=current_user.cliente_id,
        punto_venta_id=punto_venta_id,
        empresa_id=empresa_id,
        estado=estado,
        cajero_usuario_id=cajero_usuario_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.post(
    "/{turno_id}/cerrar",
    response_model=TurnoCajaRead,
    tags=["POS - Turnos de Caja"],
    summary="Cerrar turno de caja",
)
async def post_cerrar_turno_caja(
    turno_id: UUID,
    data: TurnoCajaCerrarRequest,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.cerrar")),
):
    try:
        return await cerrar_turno_caja(
            current_user.cliente_id,
            turno_id,
            data,
            cerrado_por_usuario_id=current_user.usuario_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))


@router.get("/{turno_id}", response_model=TurnoCajaRead, tags=["POS - Turnos de Caja"])
async def get_turno_caja(
    turno_id: UUID,
    empresa_id: Optional[UUID] = Query(
        None,
        description="Si se informa, la fila debe pertenecer a esta empresa.",
    ),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Obtiene un turno de caja por id."""
    try:
        return await get_turno_caja_by_id(
            current_user.cliente_id,
            turno_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=TurnoCajaRead, status_code=status.HTTP_201_CREATED, tags=["POS - Turnos de Caja"])
async def post_turno_caja(
    data: TurnoCajaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Abre un turno de caja (apertura)."""
    return await create_turno_caja(current_user.cliente_id, data)


@router.put("/{turno_id}", response_model=TurnoCajaRead, tags=["POS - Turnos de Caja"])
async def put_turno_caja(
    turno_id: UUID,
    data: TurnoCajaUpdate,
    empresa_id: Optional[UUID] = Query(
        None,
        description="Si se informa, la fila debe pertenecer a esta empresa.",
    ),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza un turno de caja (sin totales de sistema; use POST …/cerrar)."""
    try:
        return await update_turno_caja(
            current_user.cliente_id,
            turno_id,
            data,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))
