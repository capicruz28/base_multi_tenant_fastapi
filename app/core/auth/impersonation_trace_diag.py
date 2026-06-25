"""
Diagnóstico temporal RC2 — trazas de impersonación en flujos empresa/refresh.

Prefijo log: [IMPERSONATION-TRACE]
Eliminar tras cerrar investigación de regresión impersonación + cambio empresa.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from jose import JWTError, jwt

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

TRACE_PREFIX = "[IMPERSONATION-TRACE]"


def _claims_summary(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not payload:
        return {
            "is_impersonation": None,
            "impersonated_by": None,
            "sub": None,
            "cliente_id": None,
            "empresa_id": None,
        }
    return {
        "is_impersonation": bool(payload.get("is_impersonation")),
        "impersonated_by": payload.get("impersonated_by"),
        "sub": payload.get("sub"),
        "cliente_id": payload.get("cliente_id"),
        "empresa_id": payload.get("empresa_id"),
    }


def decode_access_token_claims(token: Optional[str]) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        return None


def log_impersonation_trace_request(
    *,
    endpoint: str,
    payload: Optional[Dict[str, Any]],
    jwt_kind: str = "access",
) -> None:
    claims = _claims_summary(payload)
    logger.info(
        "%s REQUEST endpoint=%s jwt_kind=%s http_status=pending "
        "is_impersonation=%s impersonated_by=%s sub=%s cliente_id=%s empresa_id=%s",
        TRACE_PREFIX,
        endpoint,
        jwt_kind,
        claims["is_impersonation"],
        claims["impersonated_by"],
        claims["sub"],
        claims["cliente_id"],
        claims["empresa_id"],
    )


def log_impersonation_trace_response(
    *,
    endpoint: str,
    http_status: int,
    request_payload: Optional[Dict[str, Any]] = None,
    issued_access_token: Optional[str] = None,
    emission_reason: Optional[str] = None,
) -> None:
    req = _claims_summary(request_payload)
    issued_claims = (
        _claims_summary(decode_access_token_claims(issued_access_token))
        if issued_access_token
        else _claims_summary(None)
    )
    logger.info(
        "%s RESPONSE endpoint=%s http_status=%s "
        "request_is_impersonation=%s request_impersonated_by=%s request_sub=%s "
        "request_cliente_id=%s request_empresa_id=%s "
        "issued_is_impersonation=%s issued_impersonated_by=%s issued_sub=%s "
        "issued_cliente_id=%s issued_empresa_id=%s emission_reason=%s",
        TRACE_PREFIX,
        endpoint,
        http_status,
        req["is_impersonation"],
        req["impersonated_by"],
        req["sub"],
        req["cliente_id"],
        req["empresa_id"],
        issued_claims["is_impersonation"] if issued_access_token else None,
        issued_claims["impersonated_by"] if issued_access_token else None,
        issued_claims["sub"] if issued_access_token else None,
        issued_claims["cliente_id"] if issued_access_token else None,
        issued_claims["empresa_id"] if issued_access_token else None,
        emission_reason,
    )
