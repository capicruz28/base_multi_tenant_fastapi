"""
Diagnóstico temporal: POST /auth/impersonate/* → 401 Not authenticated.

Solo logging; no altera auth. Activar middleware en main.py.
"""
from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.security.jwt import normalize_bearer_jwt_token

logger = logging.getLogger(__name__)

IMPERSONATE_PATH_MARKER = "/auth/impersonate"

_impersonate_diag_active: ContextVar[bool] = ContextVar(
    "impersonate_diag_active", default=False
)


def is_impersonate_diag_request() -> bool:
    return _impersonate_diag_active.get()


def _path_is_impersonate(path: str) -> bool:
    return IMPERSONATE_PATH_MARKER in path


def _safe_token_prefix(auth_header: Optional[str]) -> str:
    if not auth_header:
        return "<missing>"
    text = auth_header.strip()
    if len(text) <= 24:
        return text
    return f"{text[:24]}..."


def log_impersonate_token_claims(
    raw_authorization: Optional[str],
    *,
    phase: str,
) -> None:
    """
    Decodifica JWT solo para logs (no valida exp en prod path).
    """
    if not raw_authorization:
        logger.warning(
            "[IMPERSONATE-AUTH] %s no Authorization header — oauth2_scheme devolverá "
            "'Not authenticated' antes de get_current_user_data",
            phase,
        )
        return
    try:
        token = normalize_bearer_jwt_token(raw_authorization)
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
        claims_log = {
            k: payload.get(k)
            for k in (
                "sub",
                "cliente_id",
                "user_type",
                "es_superadmin",
                "is_super_admin",
                "access_level",
                "type",
                "exp",
                "jti",
            )
        }
        logger.info(
            "[IMPERSONATE-AUTH] %s token_decode_ok claims=%s token_len=%s",
            phase,
            claims_log,
            len(token),
        )
        if payload.get("type") == "refresh":
            logger.warning(
                "[IMPERSONATE-AUTH] %s token type=refresh (debe ser access)",
                phase,
            )
    except HTTPException as exc:
        logger.warning(
            "[IMPERSONATE-AUTH] %s normalize_bearer_failed status=%s detail=%s",
            phase,
            exc.status_code,
            exc.detail,
        )
    except JWTError as exc:
        logger.warning(
            "[IMPERSONATE-AUTH] %s jwt_decode_failed error=%s",
            phase,
            exc,
        )
    except Exception as exc:
        logger.warning(
            "[IMPERSONATE-AUTH] %s unexpected_decode_error %s:%s",
            phase,
            type(exc).__name__,
            exc,
        )


def log_impersonate_request_headers(request: Request, *, phase: str) -> None:
    auth = request.headers.get("authorization")
    logger.info(
        "[IMPERSONATE-AUTH] %s path=%s method=%s "
        "authorization_present=%s authorization_prefix=%s "
        "origin=%s host=%s cookie_names=%s",
        phase,
        request.url.path,
        request.method,
        bool(auth),
        _safe_token_prefix(auth),
        request.headers.get("origin"),
        request.headers.get("host"),
        list(request.cookies.keys()),
    )
    log_impersonate_token_claims(auth, phase=f"{phase}_claims")


def log_impersonate_payload_summary(
    payload: Dict[str, Any],
    *,
    phase: str,
) -> None:
    logger.info(
        "[IMPERSONATE-AUTH] %s payload sub=%s cliente_id=%s user_type=%s "
        "es_superadmin=%s is_super_admin=%s access_level=%s type=%s",
        phase,
        payload.get("sub"),
        payload.get("cliente_id"),
        payload.get("user_type"),
        payload.get("es_superadmin"),
        payload.get("is_super_admin"),
        payload.get("access_level"),
        payload.get("type"),
    )


class ImpersonateAuthDiagMiddleware(BaseHTTPMiddleware):
    """Loguea headers/token antes de que FastAPI resuelva oauth2_scheme."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if not _path_is_impersonate(request.url.path):
            return await call_next(request)

        token = _impersonate_diag_active.set(True)
        try:
            log_impersonate_request_headers(request, phase="middleware_pre_deps")
            response = await call_next(request)
            if response.status_code == 401:
                logger.warning(
                    "[IMPERSONATE-AUTH] middleware_post_deps response_401 path=%s "
                    "(si no hay logs get_current_user_data → falló oauth2_scheme)",
                    request.url.path,
                )
            return response
        finally:
            _impersonate_diag_active.reset(token)
