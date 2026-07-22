"""
Dependencias FastAPI del módulo CFG (sesión tenant ERP).

Patrón: clona semántica de ``require_org_tenant_erp_session`` /
``get_org_session_client_id`` (ORG) sin modificar auth/session core.
Spec: cfg-implementation-spec v1.0 — Etapa 4.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Depends, Request

from app.api.deps import get_current_active_user, get_current_user_data
from app.api.deps_auth import require_full_session_payload
from app.core.tenant.session_scope import (
    OrgScopePolicy,
    log_org_erp_session,
    require_company_scope_if_needed,
    require_session_cliente_id,
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


async def get_cfg_session_client_id(
    request: Request,
    payload: Dict[str, Any] = Depends(get_current_user_data),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
) -> UUID:
    """
    Cliente_id operativo para servicios CFG (impersonación → JWT tenant).

    Misma resolución que ``get_org_session_client_id`` vía ``require_session_cliente_id``.
    """
    return require_session_cliente_id(
        payload=payload,
        user_cliente_id=getattr(current_user, "cliente_id", None),
        request_cliente_id=_request_cliente_id(request),
        endpoint=_endpoint_label(request),
    )


async def require_cfg_tenant_erp_session(
    request: Request,
    payload: Dict[str, Any] = Depends(require_full_session_payload),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
) -> UsuarioReadWithRoles:
    """
    Sesión ERP para recursos CFG tenant-wide (/cfg/secuencias).

    No exige empresa_id activa (listado transversal multi-empresa / impersonación).
    Policy: ``OrgScopePolicy.TENANT`` (helper compartido session_scope).
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
