"""Endpoints dms documento."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.dms.application.services import (
    list_documento,
    get_documento_by_id,
    create_documento,
    update_documento,
)
from app.modules.dms.presentation.schemas import (
    DocumentoCreate,
    DocumentoUpdate,
    DocumentoRead,
)
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("", response_model=List[DocumentoRead])
async def get_documentos(
    empresa_id: Optional[UUID] = Query(None),
    tipo_documento: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    entidad_tipo: Optional[str] = Query(None),
    entidad_id: Optional[UUID] = Query(None),
    carpeta: Optional[str] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("dms.documento.leer")),
):
    return await list_documento(
        current_user.cliente_id,
        empresa_id=empresa_id,
        tipo_documento=tipo_documento,
        categoria=categoria,
        estado=estado,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        carpeta=carpeta,
        buscar=buscar,
    )


@router.get("/{documento_id}", response_model=DocumentoRead)
async def get_documento(
    documento_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("dms.documento.leer")),
):
    try:
        return await get_documento_by_id(current_user.cliente_id, documento_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=DocumentoRead, status_code=status.HTTP_201_CREATED)
async def post_documento(
    data: DocumentoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("dms.documento.crear")),
):
    return await create_documento(current_user.cliente_id, data)


@router.put("/{documento_id}", response_model=DocumentoRead)
async def put_documento(
    documento_id: UUID,
    data: DocumentoUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission("dms.documento.actualizar")),
):
    try:
        return await update_documento(current_user.cliente_id, documento_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
