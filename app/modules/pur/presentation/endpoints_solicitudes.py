# app/modules/pur/presentation/endpoints_solicitudes.py
"""Endpoints PUR - Solicitudes de Compra. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from uuid import UUID
from typing import Optional
from datetime import date

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pur.presentation.schemas import (
    SolicitudCompraCreate,
    SolicitudCompraUpdate,
    SolicitudCompraRead,
    PurMotivoRechazoBody,
    SolicitudAnularBody,
)
from app.modules.pur.application.services import solicitud_service
from app.core.exceptions import NotFoundError

MODULE_CODE = "pur"
RESOURCE_CODE = "solicitud"

router = APIRouter()


@router.get("", response_model=list[SolicitudCompraRead], summary="Listar solicitudes de compra")
async def listar_solicitudes(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    page: Optional[int] = Query(None, ge=1, description="Página (con page_size)"),
    page_size: Optional[int] = Query(None, ge=1, le=500, description="Registros por página"),
    sort_by: Optional[str] = Query(None, description="Ordenar por: fecha_solicitud, estado, numero_solicitud, fecha_creacion"),
    order: Optional[str] = Query(None, description="asc o desc"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista solicitudes de compra del tenant. Paginación opcional con page y page_size."""
    client_id = current_user.cliente_id
    return await solicitud_service.list_solicitudes_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
    )


@router.post("", response_model=SolicitudCompraRead, status_code=status.HTTP_201_CREATED, summary="Crear solicitud")
async def crear_solicitud(
    data: SolicitudCompraCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea una solicitud de compra. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await solicitud_service.create_solicitud_servicio(client_id=client_id, data=data)


@router.put("/{solicitud_id}", response_model=SolicitudCompraRead, summary="Actualizar solicitud")
async def actualizar_solicitud(
    solicitud_id: UUID,
    data: SolicitudCompraUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza una solicitud. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await solicitud_service.update_solicitud_servicio(
            client_id=client_id,
            solicitud_id=solicitud_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{solicitud_id}/aprobar", response_model=SolicitudCompraRead, summary="Aprobar solicitud")
async def aprobar_solicitud(
    solicitud_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Aprueba la solicitud de compra. Solo en estado borrador o pendiente_aprobacion."""
    client_id = current_user.cliente_id
    try:
        return await solicitud_service.aprobar_solicitud_servicio(
            client_id=client_id,
            solicitud_id=solicitud_id,
            aprobado_por_usuario_id=current_user.usuario_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{solicitud_id}/rechazar", response_model=SolicitudCompraRead, summary="Rechazar solicitud")
async def rechazar_solicitud(
    solicitud_id: UUID,
    body: Optional[PurMotivoRechazoBody] = Body(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Rechaza la solicitud de compra. Body opcional: motivo_rechazo (JSON vacío permitido)."""
    client_id = current_user.cliente_id
    body_data = body or PurMotivoRechazoBody()
    motivo_rechazo = body_data.motivo_rechazo or ""
    try:
        return await solicitud_service.rechazar_solicitud_servicio(
            client_id=client_id,
            solicitud_id=solicitud_id,
            motivo_rechazo=motivo_rechazo,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{solicitud_id}/anular", response_model=SolicitudCompraRead, summary="Anular solicitud de compra")
async def anular_solicitud(
    solicitud_id: UUID,
    body: Optional[SolicitudAnularBody] = Body(None),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Pasa la solicitud a estado anulada. Body opcional: motivo (máx. 500)."""
    client_id = current_user.cliente_id
    body_data = body or SolicitudAnularBody()
    try:
        return await solicitud_service.anular_solicitud_servicio(
            client_id=client_id,
            solicitud_id=solicitud_id,
            motivo=body_data.motivo or None,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{solicitud_id}/marcar-procesada", response_model=SolicitudCompraRead, summary="Marcar solicitud como procesada")
async def marcar_procesada_solicitud(
    solicitud_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Marca la solicitud como procesada (se generó OC)."""
    client_id = current_user.cliente_id
    try:
        return await solicitud_service.marcar_procesada_solicitud_servicio(
            client_id=client_id,
            solicitud_id=solicitud_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{solicitud_id}", response_model=SolicitudCompraRead, summary="Detalle solicitud")
async def detalle_solicitud(
    solicitud_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Detalle de una solicitud. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await solicitud_service.get_solicitud_servicio(
            client_id=client_id,
            solicitud_id=solicitud_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
