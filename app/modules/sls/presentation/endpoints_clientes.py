"""
Endpoints FastAPI para sls_cliente.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.sls.application.services import (
    list_clientes,
    get_cliente_by_id,
    create_cliente,
    update_cliente,
)
from app.modules.sls.presentation.schemas import (
    ClienteCreate,
    ClienteUpdate,
    ClienteRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[ClienteRead], tags=["SLS - Clientes"])
async def get_clientes(
    empresa_id: Optional[UUID] = Query(None),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None),
    vendedor_usuario_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Lista clientes del tenant."""
    return await list_clientes(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
        buscar=buscar,
        vendedor_usuario_id=vendedor_usuario_id
    )


@router.get("/{cliente_venta_id}", response_model=ClienteRead, tags=["SLS - Clientes"])
async def get_cliente(
    cliente_venta_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Obtiene un cliente por id."""
    try:
        return await get_cliente_by_id(current_user.cliente_id, cliente_venta_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ClienteRead, status_code=status.HTTP_201_CREATED, tags=["SLS - Clientes"])
async def post_cliente(
    data: ClienteCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea un cliente."""
    return await create_cliente(current_user.cliente_id, data)


@router.put("/{cliente_venta_id}", response_model=ClienteRead, tags=["SLS - Clientes"])
async def put_cliente(
    cliente_venta_id: UUID,
    data: ClienteUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Actualiza un cliente."""
    try:
        return await update_cliente(current_user.cliente_id, cliente_venta_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
