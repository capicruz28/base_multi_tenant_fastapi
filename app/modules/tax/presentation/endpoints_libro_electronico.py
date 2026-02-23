"""Endpoints tax libro electrónico."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.tax.application.services import (
    list_libro_electronico,
    get_libro_electronico_by_id,
    create_libro_electronico,
    update_libro_electronico,
)
from app.modules.tax.presentation.schemas import (
    LibroElectronicoCreate,
    LibroElectronicoUpdate,
    LibroElectronicoRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[LibroElectronicoRead])
async def get_libros_electronicos(
    empresa_id: Optional[UUID] = Query(None),
    tipo_libro: Optional[str] = Query(None),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    mes: Optional[int] = Query(None, ge=1, le=12),
    estado: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await list_libro_electronico(
        current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_libro=tipo_libro,
        anio=anio,
        mes=mes,
        estado=estado,
    )


@router.get("/{libro_id}", response_model=LibroElectronicoRead)
async def get_libro_electronico(
    libro_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await get_libro_electronico_by_id(current_user.cliente_id, libro_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=LibroElectronicoRead, status_code=status.HTTP_201_CREATED)
async def post_libro_electronico(
    data: LibroElectronicoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    return await create_libro_electronico(current_user.cliente_id, data)


@router.put("/{libro_id}", response_model=LibroElectronicoRead)
async def put_libro_electronico(
    libro_id: UUID,
    data: LibroElectronicoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    try:
        return await update_libro_electronico(current_user.cliente_id, libro_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
