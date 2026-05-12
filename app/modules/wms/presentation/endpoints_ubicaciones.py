"""
Endpoints FastAPI para wms_ubicacion.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.wms.application.services import (
    list_ubicaciones,
    get_ubicacion_by_id,
    create_ubicacion,
    update_ubicacion,
)
from app.modules.wms.presentation.schemas import (
    UbicacionCreate,
    UbicacionUpdate,
    UbicacionRead,
)
from app.core.exceptions import NotFoundError

MODULE_CODE = "wms"
RESOURCE_CODE = "ubicacion"

router = APIRouter()


@router.get("", response_model=List[UbicacionRead], tags=["WMS - Ubicaciones"])
async def get_ubicaciones(
    empresa_id: UUID = Query(...),
    almacen_id: Optional[UUID] = Query(None),
    zona_id: Optional[UUID] = Query(None),
    tipo_ubicacion: Optional[str] = Query(None),
    estado_ubicacion: Optional[str] = Query(None),
    es_ubicacion_picking: Optional[bool] = Query(None),
    solo_activos: bool = Query(True),
    buscar: Optional[str] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista ubicaciones del tenant."""
    return await list_ubicaciones(
        client_id=current_user.cliente_id,
        empresa_id=empresa_id,
        almacen_id=almacen_id,
        zona_id=zona_id,
        tipo_ubicacion=tipo_ubicacion,
        estado_ubicacion=estado_ubicacion,
        es_ubicacion_picking=es_ubicacion_picking,
        solo_activos=solo_activos,
        buscar=buscar
    )


@router.get("/{ubicacion_id}", response_model=UbicacionRead, tags=["WMS - Ubicaciones"])
async def get_ubicacion(
    ubicacion_id: UUID,
    empresa_id: UUID = Query(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Obtiene una ubicación por id."""
    try:
        return await get_ubicacion_by_id(current_user.cliente_id, empresa_id, ubicacion_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "",
    response_model=UbicacionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["WMS - Ubicaciones"],
    dependencies=[Depends(require_permission("wms.ubicacion.crear"))],
)
async def post_ubicacion(
    data: UbicacionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
):
    """Crea una ubicación."""
    return await create_ubicacion(current_user.cliente_id, data)


@router.put("/{ubicacion_id}", response_model=UbicacionRead, tags=["WMS - Ubicaciones"])
async def put_ubicacion(
    ubicacion_id: UUID,
    data: UbicacionUpdate,
    empresa_id: Optional[UUID] = Query(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una ubicación."""
    empresa_id_final = data.empresa_id or empresa_id
    if empresa_id_final is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empresa_id es requerido")
    try:
        return await update_ubicacion(current_user.cliente_id, empresa_id_final, ubicacion_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{ubicacion_id}/activar", response_model=UbicacionRead, tags=["WMS - Ubicaciones"])
async def post_ubicacion_activar(
    ubicacion_id: UUID,
    empresa_id: UUID = Query(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission("wms.ubicacion.actualizar")),
):
    """Activa una ubicación (es_activo = true)."""
    try:
        return await update_ubicacion(
            current_user.cliente_id,
            empresa_id,
            ubicacion_id,
            UbicacionUpdate(es_activo=True),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{ubicacion_id}/desactivar", response_model=UbicacionRead, tags=["WMS - Ubicaciones"])
async def post_ubicacion_desactivar(
    ubicacion_id: UUID,
    empresa_id: UUID = Query(...),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission("wms.ubicacion.actualizar")),
):
    """Desactiva una ubicación (es_activo = false)."""
    try:
        return await update_ubicacion(
            current_user.cliente_id,
            empresa_id,
            ubicacion_id,
            UbicacionUpdate(es_activo=False),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
