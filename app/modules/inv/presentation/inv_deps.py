"""
Dependencias FastAPI del módulo INV — sesión tenant (patrón ORG Etapa A).

Reutiliza require_session_cliente_id (impersonación → JWT tenant).
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Depends, Request

from app.api.deps import get_current_active_user, get_current_user_data
from app.core.tenant.session_scope import require_session_cliente_id
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


async def get_inv_session_client_id(
    request: Request,
    payload: Dict[str, Any] = Depends(get_current_user_data),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
) -> UUID:
    """
    Cliente_id operativo para servicios INV (impersonación → JWT tenant).

    Mismo mecanismo que get_org_session_client_id en org_deps.py.
    """
    return require_session_cliente_id(
        payload=payload,
        user_cliente_id=getattr(current_user, "cliente_id", None),
        request_cliente_id=_request_cliente_id(request),
        endpoint=_endpoint_label(request),
    )
