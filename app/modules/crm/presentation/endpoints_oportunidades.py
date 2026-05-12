"""
Endpoints FastAPI para crm_oportunidad.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.crm.application.services import (
    list_oportunidades,
    get_oportunidad_by_id,
    create_oportunidad,
    update_oportunidad,
    marcar_oportunidad_ganada,
    marcar_oportunidad_perdida,
    cancelar_oportunidad,
)
from app.modules.crm.presentation.schemas import (
    OportunidadCreate,
    OportunidadUpdate,
    OportunidadRead,
    OportunidadMarcarGanada,
    OportunidadMarcarPerdida,
    OportunidadCancelar,
)
from app.core.exceptions import NotFoundError

MODULE_CODE = "crm"
RESOURCE_CODE = "oportunidad"

router = APIRouter()


@router.get("", response_model=List[OportunidadRead], tags=["CRM - Oportunidades"])
async def get_oportunidades(
    empresa_id: Optional[UUID] = Query(None),
    cliente_venta_id: Optional[UUID] = Query(None),
    lead_id: Optional[UUID] = Query(None),
    campana_id: Optional[UUID] = Query(None),
    vendedor_usuario_id: Optional[UUID] = Query(None),
    etapa: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    tipo_oportunidad: Optional[str] = Query(None),
    fecha_cierre_desde: Optional[date] = Query(None),
    fecha_cierre_hasta: Optional[date] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista oportunidades del tenant."""
    return await list_oportunidades(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        cliente_venta_id=cliente_venta_id,
        lead_id=lead_id,
        campana_id=campana_id,
        vendedor_usuario_id=vendedor_usuario_id,
        etapa=etapa,
        estado=estado,
        tipo_oportunidad=tipo_oportunidad,
        fecha_cierre_desde=fecha_cierre_desde,
        fecha_cierre_hasta=fecha_cierre_hasta,
        buscar=buscar
    )


@router.get("/{oportunidad_id}", response_model=OportunidadRead, tags=["CRM - Oportunidades"])
async def get_oportunidad(
    oportunidad_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Obtiene una oportunidad por id."""
    try:
        return await get_oportunidad_by_id(current_user.cliente_id, oportunidad_id, empresa_id=empresa_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=OportunidadRead, status_code=status.HTTP_201_CREATED, tags=["CRM - Oportunidades"])
async def post_oportunidad(
    data: OportunidadCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una oportunidad."""
    return await create_oportunidad(current_user.cliente_id, data)


@router.put("/{oportunidad_id}", response_model=OportunidadRead, tags=["CRM - Oportunidades"])
async def put_oportunidad(
    oportunidad_id: UUID,
    data: OportunidadUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una oportunidad."""
    try:
        return await update_oportunidad(current_user.cliente_id, oportunidad_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{oportunidad_id}/marcar-ganada",
    response_model=OportunidadRead,
    tags=["CRM - Oportunidades"],
)
async def post_marcar_ganada(
    oportunidad_id: UUID,
    data: OportunidadMarcarGanada,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    try:
        return await marcar_oportunidad_ganada(
            client_id=current_user.cliente_id,
            oportunidad_id=oportunidad_id,
            data=data,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{oportunidad_id}/marcar-perdida",
    response_model=OportunidadRead,
    tags=["CRM - Oportunidades"],
)
async def post_marcar_perdida(
    oportunidad_id: UUID,
    data: OportunidadMarcarPerdida,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    try:
        return await marcar_oportunidad_perdida(
            client_id=current_user.cliente_id,
            oportunidad_id=oportunidad_id,
            data=data,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{oportunidad_id}/cancelar",
    response_model=OportunidadRead,
    tags=["CRM - Oportunidades"],
)
async def post_cancelar(
    oportunidad_id: UUID,
    data: OportunidadCancelar,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    try:
        return await cancelar_oportunidad(
            client_id=current_user.cliente_id,
            oportunidad_id=oportunidad_id,
            data=data,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
