"""
Dependencias JWT para flujo multi-empresa (selection token vs sesión ERP completa).

Rutas que aceptan **selection token** (`empresa_selection_pending=true`):
  - POST /auth/empresa/seleccionar/

GET /auth/me/ con selection token → **409**, salvo sesión de impersonación (`is_impersonation`).

Rutas con **sesión ERP completa** (require_erp_session / require_full_session_payload):
  - POST /auth/empresa/cambiar/
  - GET  /auth/permissions/me
  - GET  /auth/menu
  - Módulo INV (router dependency)
  - Módulo ORG company-scoped (require_org_company_erp_session en sub-routers)
  - ORG tenant-wide (/org/empresa): require_org_tenant_erp_session (sin empresa obligatoria)
  - Resto de endpoints ERP operativos (migración gradual en fases posteriores)

Matriz sin empresa_id obligatorio (ver validate_erp_operational_session):
  - platform_admin / superadmin plataforma (es_superadmin)
  - Rutas auth de login, refresh, selección (no usan require_erp_session)
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from app.api.deps import get_current_active_user, get_current_user_data
from app.core.config import settings
from app.core.tenant.company_scope import validate_erp_operational_session
from app.modules.users.presentation.schemas import UsuarioReadWithRoles

_SESSION_UNAUTHORIZED_DETAIL = (
    "Sesión expirada o cerrada remotamente. Por favor, vuelva a iniciar sesión."
)


def _coerce_uuid(value: Any) -> Optional[UUID]:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


async def _extract_refresh_token_for_me_probe(request: Request) -> Optional[str]:
    client_type = request.headers.get("X-Client-Type", "web").lower()
    if client_type == "web":
        return request.cookies.get(settings.REFRESH_COOKIE_NAME)
    try:
        body = await request.json()
        if isinstance(body, dict):
            refresh = body.get("refresh_token")
            if refresh:
                return str(refresh)
    except Exception:
        pass
    return None


async def require_selection_token_payload(
    payload: Dict[str, Any] = Depends(get_current_user_data),
) -> Dict[str, Any]:
    """
    Exige access token temporal emitido tras login multi-empresa.
    """
    if payload.get("type") and payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido para selección de empresa",
        )
    if not payload.get("empresa_selection_pending"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "El token no es de selección de empresa. "
                "Use el access token de sesión activa o inicie sesión de nuevo."
            ),
        )
    return payload


async def require_full_session_payload(
    payload: Dict[str, Any] = Depends(get_current_user_data),
) -> Dict[str, Any]:
    """
    Rechaza selection tokens en endpoints que requieren sesión ERP completa,
    salvo impersonación de soporte (permite menu/permissions con selection pendiente).
    """
    from app.core.auth.impersonation import is_impersonation_payload

    if payload.get("empresa_selection_pending") and not is_impersonation_payload(
        payload
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Debe completar la selección de empresa antes de acceder a este recurso. "
                "Use POST /api/v1/auth/empresa/seleccionar/."
            ),
        )
    return payload


async def require_erp_session(
    request: Request,
    payload: Dict[str, Any] = Depends(require_full_session_payload),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
) -> UsuarioReadWithRoles:
    """
    Contrato I1 — sesión ERP operativa para el request actual.

    Garantiza:
      - JWT válido y usuario activo (vía get_current_active_user + I0 ContextVar)
      - No es selection token (empresa_selection_pending=false)
      - empresa_id presente en sesión salvo platform_operator documentado

    Compatible con require_permission: ambos comparten get_current_active_user (cache FastAPI).
    """
    try:
        validate_erp_operational_session(
            payload=payload,
            user_type=getattr(current_user, "user_type", "user"),
            is_super_admin=getattr(current_user, "is_super_admin", False),
        )
    except Exception as exc:
        from app.core.exceptions import CustomException

        if isinstance(exc, CustomException):
            raise HTTPException(
                status_code=exc.status_code,
                detail=exc.detail,
            ) from exc
        raise
    return current_user


async def get_current_active_user_full_session(
    request: Request,
    _payload_ok: Dict[str, Any] = Depends(require_full_session_payload),
    current_user: UsuarioReadWithRoles = Depends(get_current_active_user),
) -> UsuarioReadWithRoles:
    """
    Usuario activo con sesión completa (sin selection token).

    Preferir require_erp_session en rutas ERP operativas (incluye validación empresa_id).
    """
    return current_user


async def reject_selection_token_for_me(
    payload: Dict[str, Any] = Depends(get_current_user_data),
) -> Dict[str, Any]:
    """
    GET /auth/me no admite selection_token; usar POST /auth/empresa/seleccionar/.
    Excepción: sesión de impersonación de soporte.
    """
    from app.core.auth.impersonation import is_impersonation_payload

    if payload.get("empresa_selection_pending") and not is_impersonation_payload(
        payload
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Debe seleccionar una empresa antes de continuar. "
                "Use POST /api/v1/auth/empresa/seleccionar/ con el selection_token."
            ),
        )
    return payload


async def require_active_password_session_v2_for_me(
    request: Request,
    payload: Dict[str, Any] = Depends(reject_selection_token_for_me),
) -> Dict[str, Any]:
    """
    GET /auth/me — ResolveSessionContext (V2): rechaza sesión password revocada vía probe.

    Fail-soft si no hay refresh en el request o el probe no resuelve session_id.
    """
    from app.core.auth.impersonation import is_impersonation_payload
    from app.modules.auth.application.session.session_v2_feature import (
        is_session_v2_enabled,
    )

    if is_impersonation_payload(payload):
        return payload

    cliente_id = _coerce_uuid(payload.get("cliente_id"))
    if not cliente_id or not is_session_v2_enabled(cliente_id):
        return payload

    refresh_token = await _extract_refresh_token_for_me_probe(request)
    if not refresh_token:
        return payload

    from app.modules.auth.application.services.session_probe_service import (
        SessionProbeService,
    )

    probe = await SessionProbeService.resolve_context(
        cliente_id,
        refresh_token=refresh_token,
    )
    if probe.current_session_id is not None and not probe.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_SESSION_UNAUTHORIZED_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload
