"""
Dependencias FastAPI del módulo ORG (Etapa A — sesión tenant/company).

Separado de deps_auth global para no alterar INV ni auth core.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Query, Request, status

from app.api.deps import get_current_active_user, get_current_user_data
from app.api.deps_auth import require_full_session_payload
from app.core.exceptions import AuthorizationError, CustomException
from app.core.tenant.company_scope import (
    reject_client_empresa_scope_override,
    _coerce_cliente_id,
)
from app.core.tenant.session_scope import (
    OrgScopePolicy,
    log_org_erp_session,
    require_company_scope_if_needed,
    require_session_cliente_id,
    resolve_org_scope_policy,
)
from app.modules.users.presentation.schemas import UsuarioReadWithRoles


def _request_cliente_id(request: Request) -> Optional[UUID]:
    raw = getattr(request.state, "cliente_id", None)
    if raw is None:
        return None
    try:
        return UUID(str(raw))
    except (ValueError, TypeError):
        return None


def _endpoint_label(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None) or request.url.path
    return f"{request.method} {path}"


async def get_org_session_client_id(
    request: Request,
    payload: Dict[str, Any] = Depends(get_current_user_data),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
) -> UUID:
    """
    Cliente_id operativo para servicios ORG (impersonación → JWT tenant).
    """
    return require_session_cliente_id(
        payload=payload,
        user_cliente_id=getattr(current_user, "cliente_id", None),
        request_cliente_id=_request_cliente_id(request),
        endpoint=_endpoint_label(request),
    )


async def require_org_tenant_erp_session(
    request: Request,
    payload: Dict[str, Any] = Depends(require_full_session_payload),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
) -> UsuarioReadWithRoles:
    """
    Sesión ERP para recursos tenant-wide (/org/empresa).

    No exige empresa_id activa (multi-empresa admin, impersonación sin selección).
    """
    session_cid = require_session_cliente_id(
        payload=payload,
        user_cliente_id=getattr(current_user, "cliente_id", None),
        request_cliente_id=_request_cliente_id(request),
        endpoint=_endpoint_label(request),
    )
    require_company_scope_if_needed(
        policy=OrgScopePolicy.TENANT,
        payload=payload,
        user_type=getattr(current_user, "user_type", "user"),
        is_super_admin=getattr(current_user, "is_super_admin", False),
        endpoint=_endpoint_label(request),
    )
    log_org_erp_session(
        endpoint=_endpoint_label(request),
        scope_kind="tenant",
        payload=payload,
        session_cliente_id=session_cid,
    )
    return current_user


async def require_org_company_erp_session(
    request: Request,
    payload: Dict[str, Any] = Depends(require_full_session_payload),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
) -> UsuarioReadWithRoles:
    """
    Sesión ERP para recursos company-scoped e híbridos operativos.

    Impersonación + empresa_selection_pending → 403 MISSING_SESSION_EMPRESA.
    """
    session_cid = require_session_cliente_id(
        payload=payload,
        user_cliente_id=getattr(current_user, "cliente_id", None),
        request_cliente_id=_request_cliente_id(request),
        endpoint=_endpoint_label(request),
    )
    resource = _org_resource_from_path(request.url.path)
    policy = resolve_org_scope_policy(resource=resource)
    try:
        require_company_scope_if_needed(
            policy=policy,
            payload=payload,
            user_type=getattr(current_user, "user_type", "user"),
            is_super_admin=getattr(current_user, "is_super_admin", False),
            endpoint=_endpoint_label(request),
        )
    except CustomException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    log_org_erp_session(
        endpoint=_endpoint_label(request),
        scope_kind=policy.value,
        payload=payload,
        session_cliente_id=session_cid,
    )
    return current_user


def reject_legacy_empresa_query(
    empresa_id: Optional[UUID] = Query(None, include_in_schema=False),
) -> None:
    """
    Etapa B: rechaza empresa_id en query (legacy).
    No aparece en OpenAPI; si el cliente lo envía distinto a sesión → 403.
    """
    reject_client_empresa_scope_override(empresa_id, source="query")


def user_can_manage_global_parametros(
    current_user: UsuarioReadWithRoles,
    payload: Dict[str, Any],
) -> bool:
    """
    Escritura de parámetros globales (empresa_id NULL).

    platform_operator, tenant_admin o nivel >= 4 (incl. impersonación efectiva tenant_admin).
    Usuario ERP operativo normal: solo overrides con empresa en sesión.
    """
    from app.core.auth.impersonation import is_impersonation_payload
    from app.core.tenant.company_scope import is_platform_operator

    if is_platform_operator(
        payload=payload,
        user_type=getattr(current_user, "user_type", "user"),
        is_super_admin=getattr(current_user, "is_super_admin", False),
    ):
        return True
    if is_impersonation_payload(payload):
        return int(getattr(current_user, "access_level", 0) or 0) >= 4
    if getattr(current_user, "user_type", "") == "tenant_admin":
        return True
    if int(getattr(current_user, "access_level", 0) or 0) >= 4:
        return True
    return False


def reject_legacy_cliente_query(
    cliente_id: Optional[UUID] = Query(None, include_in_schema=False),
    session_client_id: UUID = Depends(get_org_session_client_id),
) -> None:
    """
    Etapa C1: rechaza cliente_id en query (legacy) distinto al tenant de sesión.
    """
    if cliente_id is None:
        return
    query_cliente = _coerce_cliente_id(cliente_id)
    if query_cliente is not None and query_cliente != session_client_id:
        raise AuthorizationError(
            detail="cliente_id de query no coincide con el tenant activo de la sesión.",
            internal_code="TENANT_SCOPE_MISMATCH",
        )


def _org_resource_from_path(path: str) -> str:
    """Extrae segmento de recurso bajo /org/ (ej. sucursales, empresa)."""
    parts = [p for p in path.replace("\\", "/").split("/") if p]
    if "org" in parts:
        idx = parts.index("org")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return ""
