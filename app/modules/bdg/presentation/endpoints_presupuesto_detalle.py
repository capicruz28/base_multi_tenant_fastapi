"""Endpoints bdg presupuesto detalle."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.bdg.application.services import (
    list_presupuesto_detalle,
    get_presupuesto_detalle_by_id,
    create_presupuesto_detalle,
    update_presupuesto_detalle,
)
from app.modules.bdg.presentation.schemas import (
    PresupuestoDetalleCreate,
    PresupuestoDetalleUpdate,
    PresupuestoDetalleRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PresupuestoDetalleRead])
async def get_presupuestos_detalle(
    presupuesto_id: Optional[UUID] = Query(None),
    cuenta_id: Optional[UUID] = Query(None),
    centro_costo_id: Optional[UUID] = Query(None),
    mes: Optional[int] = Query(None, ge=1, le=12),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_presupuesto_detalle(
        current_user.cliente_id,
        presupuesto_id=presupuesto_id,
        cuenta_id=cuenta_id,
        centro_costo_id=centro_costo_id,
        mes=mes,
    )


@router.get("/{presupuesto_detalle_id}", response_model=PresupuestoDetalleRead)
async def get_presupuesto_detalle(
    presupuesto_detalle_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_presupuesto_detalle_by_id(
            current_user.cliente_id, presupuesto_detalle_id
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PresupuestoDetalleRead, status_code=status.HTTP_201_CREATED)
async def post_presupuesto_detalle(
    data: PresupuestoDetalleCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_presupuesto_detalle(current_user.cliente_id, data)


@router.put("/{presupuesto_detalle_id}", response_model=PresupuestoDetalleRead)
async def put_presupuesto_detalle(
    presupuesto_detalle_id: UUID,
    data: PresupuestoDetalleUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_presupuesto_detalle(
            current_user.cliente_id, presupuesto_detalle_id, data
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
