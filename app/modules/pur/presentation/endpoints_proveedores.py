# app/modules/pur/presentation/endpoints_proveedores.py
"""Endpoints PUR - Proveedores. client_id siempre desde current_user.cliente_id."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.api.deps import get_current_active_user
from app.core.authorization.rbac import require_permission
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.pur.presentation.schemas import ProveedorCreate, ProveedorUpdate, ProveedorRead
from app.modules.pur.application.services import proveedor_service
from app.core.exceptions import NotFoundError

MODULE_CODE = "pur"
RESOURCE_CODE = "proveedor"

router = APIRouter()


@router.get("", response_model=list[ProveedorRead], summary="Listar proveedores")
async def listar_proveedores(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    solo_activos: bool = Query(True, description="Solo proveedores activos"),
    buscar: Optional[str] = Query(None, description="Búsqueda por razón social, RUC o código"),
    tipo_proveedor: Optional[str] = Query(None, description="Filtrar por tipo (ej. bienes, servicios)"),
    categoria_proveedor: Optional[str] = Query(None, description="Filtrar por categoría"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (ej. activo, bloqueado)"),
    page: Optional[int] = Query(None, ge=1, description="Página (con page_size)"),
    page_size: Optional[int] = Query(None, ge=1, le=500, description="Registros por página"),
    sort_by: Optional[str] = Query(None, description="Ordenar por: razon_social, codigo_proveedor, fecha_creacion, numero_documento"),
    order: Optional[str] = Query(None, description="asc o desc"),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Lista proveedores del tenant. Filtros opcionales: tipo, categoría, estado. Paginación con page y page_size."""
    client_id = current_user.cliente_id
    return await proveedor_service.list_proveedores_servicio(
        client_id=client_id,
        empresa_id=empresa_id,
        solo_activos=solo_activos,
        buscar=buscar,
        tipo_proveedor=tipo_proveedor,
        categoria_proveedor=categoria_proveedor,
        estado=estado,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
    )


@router.get("/{proveedor_id}", response_model=ProveedorRead, summary="Detalle proveedor")
async def detalle_proveedor(
    proveedor_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.leer")),
):
    """Detalle de un proveedor. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await proveedor_service.get_proveedor_servicio(
            client_id=client_id,
            proveedor_id=proveedor_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=ProveedorRead, status_code=status.HTTP_201_CREATED, summary="Crear proveedor")
async def crear_proveedor(
    data: ProveedorCreate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.crear")),
):
    """Crea un proveedor. cliente_id se asigna desde el contexto (tenant), no desde el body."""
    client_id = current_user.cliente_id
    return await proveedor_service.create_proveedor_servicio(client_id=client_id, data=data)


@router.put("/{proveedor_id}", response_model=ProveedorRead, summary="Actualizar proveedor")
async def actualizar_proveedor(
    proveedor_id: UUID,
    data: ProveedorUpdate,
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
    _: None = Depends(require_permission(f"{MODULE_CODE}.{RESOURCE_CODE}.actualizar")),
):
    """Actualiza un proveedor. Solo del tenant del usuario."""
    client_id = current_user.cliente_id
    try:
        return await proveedor_service.update_proveedor_servicio(
            client_id=client_id,
            proveedor_id=proveedor_id,
            data=data,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
