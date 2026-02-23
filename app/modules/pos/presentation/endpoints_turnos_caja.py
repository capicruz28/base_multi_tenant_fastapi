"""
Endpoints FastAPI para pos_turno_caja.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pos.application.services import (
    list_turnos_caja,
    get_turno_caja_by_id,
    create_turno_caja,
    update_turno_caja,
)
from app.modules.pos.presentation.schemas import (
    TurnoCajaCreate,
    TurnoCajaUpdate,
    TurnoCajaRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[TurnoCajaRead], tags=["POS - Turnos de Caja"])
async def get_turnos_caja(
    punto_venta_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    cajero_usuario_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista turnos de caja del tenant."""
    return await list_turnos_caja(
        client_id=current_user.cliente_id,
        punto_venta_id=punto_venta_id,
        estado=estado,
        cajero_usuario_id=cajero_usuario_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


@router.get("/{turno_id}", response_model=TurnoCajaRead, tags=["POS - Turnos de Caja"])
async def get_turno_caja(
    turno_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un turno de caja por id."""
    try:
        return await get_turno_caja_by_id(current_user.cliente_id, turno_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=TurnoCajaRead, status_code=status.HTTP_201_CREATED, tags=["POS - Turnos de Caja"])
async def post_turno_caja(
    data: TurnoCajaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Abre un turno de caja (apertura)."""
    return await create_turno_caja(current_user.cliente_id, data)


@router.put("/{turno_id}", response_model=TurnoCajaRead, tags=["POS - Turnos de Caja"])
async def put_turno_caja(
    turno_id: UUID,
    data: TurnoCajaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un turno de caja (ej. cierre)."""
    try:
        return await update_turno_caja(current_user.cliente_id, turno_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
