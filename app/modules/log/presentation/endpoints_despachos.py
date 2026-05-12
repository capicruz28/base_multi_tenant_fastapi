"""
Endpoints FastAPI para log_despacho y log_despacho_guia.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.log.application.services import (
    list_despachos,
    get_despacho_by_id,
    create_despacho,
    update_despacho,
    completar_despacho,
    anular_despacho,
    list_despacho_guias,
    get_despacho_guia_by_id,
    create_despacho_guia,
    update_despacho_guia,
)
from app.modules.log.presentation.schemas import (
    DespachoCreate,
    DespachoUpdate,
    DespachoRead,
    DespachoGuiaCreate,
    DespachoGuiaUpdate,
    DespachoGuiaRead,
)
from app.core.exceptions import NotFoundError
from app.core.exceptions import ValidationError

router = APIRouter()

MODULE_CODE = "log"
RESOURCE_CODE = "despacho"
RESOURCE_CODE_DESPACHO_GUIA = "despacho_guia"


# ============================================================================
# DESPACHOS
# ============================================================================

@router.get("", response_model=List[DespachoRead], tags=["LOG - Despachos"])
async def get_despachos(
    empresa_id: Optional[UUID] = Query(None),
    estado: Optional[str] = Query(None),
    ruta_id: Optional[UUID] = Query(None),
    vehiculo_id: Optional[UUID] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista despachos del tenant."""
    return await list_despachos(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        estado=estado,
        ruta_id=ruta_id,
        vehiculo_id=vehiculo_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        buscar=buscar
    )


@router.get("/{despacho_id}", response_model=DespachoRead, tags=["LOG - Despachos"])
async def get_despacho(
    despacho_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Obtiene un despacho por id."""
    try:
        return await get_despacho_by_id(
            current_user.cliente_id,
            despacho_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=DespachoRead, status_code=status.HTTP_201_CREATED, tags=["LOG - Despachos"])
async def post_despacho(
    data: DespachoCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea un despacho."""
    return await create_despacho(current_user.cliente_id, data)


@router.put("/{despacho_id}", response_model=DespachoRead, tags=["LOG - Despachos"])
async def put_despacho(
    despacho_id: UUID,
    data: DespachoUpdate,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza un despacho."""
    try:
        return await update_despacho(
            current_user.cliente_id,
            despacho_id,
            data,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{despacho_id}/completar",
    response_model=DespachoRead,
    status_code=status.HTTP_200_OK,
    tags=["LOG - Despachos"],
)
async def post_completar_despacho(
    despacho_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Marca el despacho como completado."""
    try:
        return await completar_despacho(
            current_user.cliente_id,
            despacho_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/{despacho_id}/anular",
    response_model=DespachoRead,
    status_code=status.HTTP_200_OK,
    tags=["LOG - Despachos"],
)
async def post_anular_despacho(
    despacho_id: UUID,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Marca el despacho como cancelado."""
    try:
        return await anular_despacho(
            current_user.cliente_id,
            despacho_id,
            empresa_id=empresa_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# ============================================================================
# DESPACHO-GUÍA
# ============================================================================

@router.get("/{despacho_id}/guias", response_model=List[DespachoGuiaRead], tags=["LOG - Despacho-Guía"])
async def get_despacho_guias(
    despacho_id: UUID,
    estado_entrega: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE_DESPACHO_GUIA}.leer")),
):
    """Lista guías de un despacho."""
    return await list_despacho_guias(
        client_id=current_user.cliente_id,
        despacho_id=despacho_id,
        estado_entrega=estado_entrega
    )


@router.post("/{despacho_id}/guias", response_model=DespachoGuiaRead, status_code=status.HTTP_201_CREATED, tags=["LOG - Despacho-Guía"])
async def post_despacho_guia(
    despacho_id: UUID,
    data: DespachoGuiaCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE_DESPACHO_GUIA}.crear")),
):
    """Crea una relación despacho-guía."""
    data.despacho_id = despacho_id
    return await create_despacho_guia(current_user.cliente_id, data)


@router.get("/guias/{despacho_guia_id}", response_model=DespachoGuiaRead, tags=["LOG - Despacho-Guía"])
async def get_despacho_guia(
    despacho_guia_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE_DESPACHO_GUIA}.leer")),
):
    """Obtiene una relación despacho-guía por id."""
    try:
        return await get_despacho_guia_by_id(current_user.cliente_id, despacho_guia_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/guias/{despacho_guia_id}", response_model=DespachoGuiaRead, tags=["LOG - Despacho-Guía"])
async def put_despacho_guia(
    despacho_guia_id: UUID,
    data: DespachoGuiaUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: UsuarioReadWithRoles = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE_DESPACHO_GUIA}.actualizar")),
):
    """Actualiza una relación despacho-guía."""
    try:
        return await update_despacho_guia(current_user.cliente_id, despacho_guia_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
