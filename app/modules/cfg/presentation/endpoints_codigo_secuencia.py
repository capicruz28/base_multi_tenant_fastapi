"""Endpoints HTTP de secuencias de código (cfg).

Spec: cfg-implementation-spec/02_API_SPEC.md v1.0 — Etapa 7.
Solo orquesta deps + services; sin lógica de negocio.
"""

from __future__ import annotations

from typing import Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.authorization.rbac import require_permission
from app.core.exceptions import AuthorizationError, CustomException, NotFoundError
from app.modules.cfg.application.services import codigo_secuencia_admin_servicio as svc
from app.modules.cfg.presentation.cfg_deps import get_cfg_session_client_id
from app.modules.cfg.presentation.schemas import (
    CodigoSecuenciaPreviewResponse,
    CodigoSecuenciaRead,
    CodigoSecuenciaUpdate,
    PaginatedCodigoSecuenciaResponse,
)
from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.shared.pagination import (
    ErpPaginationParams,
    ErpSortParams,
    erp_pagination_params,
    erp_sort_params,
)

router = APIRouter()


@router.get(
    "",
    response_model=Union[list[CodigoSecuenciaRead], PaginatedCodigoSecuenciaResponse],
    summary="Listar secuencias de código",
    operation_id="list_cfg_codigo_secuencias",
)
async def listar_secuencias(
    empresa_id: Optional[UUID] = Query(None),
    scope_type: Optional[str] = Query(
        None,
        description="TENANT | EMPRESA | ALMACEN | PUNTO_VENTA",
    ),
    sequence_key: Optional[str] = Query(None),
    es_activo: Optional[bool] = Query(None),
    modulo_codigo: Optional[str] = Query(None),
    buscar: Optional[str] = Query(None),
    pagination: ErpPaginationParams = Depends(erp_pagination_params),
    sort: ErpSortParams = Depends(erp_sort_params),
    _: UsuarioReadWithRoles = Depends(
        require_permission("cfg.secuencias.consultar")
    ),
    client_id: UUID = Depends(get_cfg_session_client_id),
):
    try:
        return await svc.list_codigo_secuencias_servicio(
            cliente_id=client_id,
            empresa_id=empresa_id,
            scope_type=scope_type,
            sequence_key=sequence_key,
            es_activo=es_activo,
            buscar=buscar,
            modulo_codigo=modulo_codigo,
            pagination=pagination,
            sort=sort,
        )
    except CustomException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.get(
    "/{secuencia_id}",
    response_model=CodigoSecuenciaRead,
    summary="Detalle de secuencia de código",
    operation_id="get_cfg_codigo_secuencia",
)
async def detalle_secuencia(
    secuencia_id: UUID,
    _: UsuarioReadWithRoles = Depends(
        require_permission("cfg.secuencias.consultar")
    ),
    client_id: UUID = Depends(get_cfg_session_client_id),
):
    try:
        return await svc.get_codigo_secuencia_servicio(
            cliente_id=client_id,
            secuencia_id=secuencia_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.patch(
    "/{secuencia_id}",
    response_model=CodigoSecuenciaRead,
    summary="Actualizar configuración de secuencia",
    operation_id="update_cfg_codigo_secuencia",
)
async def actualizar_secuencia(
    secuencia_id: UUID,
    data: CodigoSecuenciaUpdate,
    current_user: UsuarioReadWithRoles = Depends(
        require_permission("cfg.secuencias.actualizar")
    ),
    client_id: UUID = Depends(get_cfg_session_client_id),
):
    try:
        return await svc.update_codigo_secuencia_servicio(
            cliente_id=client_id,
            secuencia_id=secuencia_id,
            data=data,
            usuario_id=current_user.usuario_id,
        )
    except (NotFoundError, AuthorizationError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.delete(
    "/{secuencia_id}",
    response_model=CodigoSecuenciaRead,
    summary="Desactivar secuencia (soft)",
    operation_id="desactivar_cfg_codigo_secuencia",
)
async def desactivar_secuencia(
    secuencia_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(
        require_permission("cfg.secuencias.actualizar")
    ),
    client_id: UUID = Depends(get_cfg_session_client_id),
):
    try:
        return await svc.desactivar_codigo_secuencia_servicio(
            cliente_id=client_id,
            secuencia_id=secuencia_id,
            usuario_id=current_user.usuario_id,
        )
    except (NotFoundError, AuthorizationError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.post(
    "/{secuencia_id}/reactivar",
    response_model=CodigoSecuenciaRead,
    summary="Reactivar secuencia",
    operation_id="reactivar_cfg_codigo_secuencia",
)
async def reactivar_secuencia(
    secuencia_id: UUID,
    current_user: UsuarioReadWithRoles = Depends(
        require_permission("cfg.secuencias.actualizar")
    ),
    client_id: UUID = Depends(get_cfg_session_client_id),
):
    try:
        return await svc.reactivar_codigo_secuencia_servicio(
            cliente_id=client_id,
            secuencia_id=secuencia_id,
            usuario_id=current_user.usuario_id,
        )
    except (NotFoundError, AuthorizationError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.post(
    "/{secuencia_id}/preview",
    response_model=CodigoSecuenciaPreviewResponse,
    summary="Previsualizar próximo código",
    operation_id="preview_cfg_codigo_secuencia",
)
async def preview_secuencia(
    secuencia_id: UUID,
    _: UsuarioReadWithRoles = Depends(
        require_permission("cfg.secuencias.consultar")
    ),
    client_id: UUID = Depends(get_cfg_session_client_id),
):
    try:
        return await svc.preview_codigo_secuencia_servicio(
            cliente_id=client_id,
            secuencia_id=secuencia_id,
        )
    except (NotFoundError, CustomException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
