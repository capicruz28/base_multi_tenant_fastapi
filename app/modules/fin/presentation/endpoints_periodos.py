"""
Endpoints FastAPI para fin_periodo_contable.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.fin.application.services import (
    list_periodos_contables,
    get_periodo_contable_by_id,
    create_periodo_contable,
    update_periodo_contable,
)
from app.modules.fin.presentation.schemas import (
    PeriodoContableCreate,
    PeriodoContableUpdate,
    PeriodoContableRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[PeriodoContableRead], tags=["FIN - Periodos Contables"])
async def get_periodos_contables(
    empresa_id: Optional[UUID] = Query(None),
    año: Optional[int] = Query(None),
    mes: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista periodos contables del tenant."""
    return await list_periodos_contables(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        año=año,
        mes=mes,
        estado=estado
    )


@router.get("/{periodo_id}", response_model=PeriodoContableRead, tags=["FIN - Periodos Contables"])
async def get_periodo_contable(
    periodo_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un periodo contable por id."""
    try:
        return await get_periodo_contable_by_id(current_user.cliente_id, periodo_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=PeriodoContableRead, status_code=status.HTTP_201_CREATED, tags=["FIN - Periodos Contables"])
async def post_periodo_contable(
    data: PeriodoContableCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un periodo contable."""
    return await create_periodo_contable(current_user.cliente_id, data)


@router.put("/{periodo_id}", response_model=PeriodoContableRead, tags=["FIN - Periodos Contables"])
async def put_periodo_contable(
    periodo_id: UUID,
    data: PeriodoContableUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un periodo contable."""
    try:
        return await update_periodo_contable(current_user.cliente_id, periodo_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
