# app/modules/pur/presentation/endpoints_recepciones.py
"""Endpoints PUR - Recepciones. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional
from datetime import date

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pur.presentation.schemas import RecepcionCreate, RecepcionUpdate, RecepcionRead
from app.modules.pur.application.services import recepcion_service
from app.core.exceptions import NotFoundError

MODULE_CODE = "pur"
RESOURCE_CODE = "recepcion"

router = APIRouter()


@router.get("", response_model=list[RecepcionRead], summary="Listar recepciones")
async def listar_recepciones(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    orden_compra_id: Optional[UUID] = Query(None, description="Filtrar por orden de compra"),
    proveedor_id: Optional[UUID] = Query(None, description="Filtrar por proveedor"),
    almacen_id: Optional[UUID] = Query(None, description="Filtrar por almacén"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    page: Optional[int] = Query(None, ge=1, description="Página (con page_size)"),
    page_size: Optional[int] = Query(None, ge=1, le=500, description="Registros por página"),
    sort_by: Optional[str] = Query(None, description="Ordenar por: fecha_recepcion, estado, numero_recepcion, fecha_creacion"),
    order: Optional[str] = Query(None, description="asc o desc"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista recepciones del tenant. Paginación opcional con page y page_size."""
    client_id = current_user.cliente_id
    return await recepcion_service.list_recepciones_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        orden_compra_id=orden_compra_id,
        proveedor_id=proveedor_id,
        almacen_id=almacen_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
    )


@router.get("/{recepcion_id}", response_model=RecepcionRead, summary="Detalle recepción")
async def detalle_recepcion(
    recepcion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Detalle de una recepción. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await recepcion_service.get_recepcion_servicio(
            client_id=client_id,
            recepcion_id=recepcion_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=RecepcionRead, status_code=status.HTTP_201_CREATED, summary="Crear recepción")
async def crear_recepcion(
    data: RecepcionCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una recepción. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await recepcion_service.create_recepcion_servicio(client_id=client_id, data=data)


@router.put("/{recepcion_id}", response_model=RecepcionRead, summary="Actualizar recepción")
async def actualizar_recepcion(
    recepcion_id: UUID,
    data: RecepcionUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una recepción. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await recepcion_service.update_recepcion_servicio(
            client_id=client_id,
            recepcion_id=recepcion_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{recepcion_id}/procesar", response_model=RecepcionRead, summary="Procesar recepción")
async def procesar_recepcion(
    recepcion_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Marca la recepción como procesada (estado=procesada, fecha y usuario de procesado)."""
    client_id = current_user.cliente_id
    try:
        return await recepcion_service.procesar_recepcion_servicio(
            client_id=client_id,
            recepcion_id=recepcion_id,
            usuario_procesado_id=current_user.usuario_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
