"""
Resolución de cliente_id y políticas de alcance para módulo ORG (Etapa A).

Blueprint alineado a INV (empresa_context + company_scope) sin sustituir aún
filtros empresa_id en queries/servicios (Etapa B).

Prioridad de tenant operativo (resolve_session_cliente_id):
  1. JWT cliente_id — solo si is_impersonation (tenant impersonado)
  2. request.state / TenantMiddleware (request_cliente_id)
  3. ContextVar tenant (try_get_current_client_id)
  4. current_user.cliente_id (fila BD; legacy fuera de impersonación)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.auth.impersonation import is_impersonation_payload
from app.core.auth.impersonation_rbac import is_impersonation_effective_tenant_session
from app.core.config import settings
from app.core.exceptions import AuthorizationError
from app.core.tenant.empresa_context import coerce_empresa_id, try_get_current_empresa_id

logger = logging.getLogger(__name__)


class OrgScopePolicy(str, Enum):
    """Alcance de datos ORG por sub-recurso."""

    TENANT = "tenant"
    COMPANY = "company"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class SessionClienteResolution:
    """Resultado de resolve_session_cliente_id."""

    cliente_id: UUID
    source: str
    is_impersonation: bool


def _coerce_cliente_uuid(value: Any) -> Optional[UUID]:
    if value is None:
        return None
    if isinstance(value, UUID):
        null_uuid = UUID("00000000-0000-0000-0000-000000000000")
        return None if value == null_uuid else value
    try:
        parsed = UUID(str(value).strip())
        null_uuid = UUID("00000000-0000-0000-0000-000000000000")
        return None if parsed == null_uuid else parsed
    except (ValueError, AttributeError, TypeError):
        return None


def resolve_session_cliente_id(
    *,
    payload: Optional[Dict[str, Any]] = None,
    user_cliente_id: Optional[UUID] = None,
    request_cliente_id: Optional[UUID] = None,
) -> SessionClienteResolution:
    """
    Cliente_id efectivo para operaciones de datos del request.

    En impersonación usa el tenant del JWT, no la fila platform (SYSTEM).
    Fuera de impersonación mantiene comportamiento legacy (request → user).
    """
    is_imp = is_impersonation_payload(payload)

    if is_imp and is_impersonation_effective_tenant_session(payload):
        jwt_cliente = _coerce_cliente_uuid((payload or {}).get("cliente_id"))
        if jwt_cliente is not None:
            return SessionClienteResolution(
                cliente_id=jwt_cliente,
                source="jwt_impersonation",
                is_impersonation=True,
            )

    req_cliente = _coerce_cliente_uuid(request_cliente_id)
    if req_cliente is not None:
        return SessionClienteResolution(
            cliente_id=req_cliente,
            source="request_tenant",
            is_impersonation=is_imp,
        )

    from app.core.tenant.context import try_get_current_client_id

    ctx_cliente = try_get_current_client_id()
    if ctx_cliente is not None:
        return SessionClienteResolution(
            cliente_id=ctx_cliente,
            source="tenant_context",
            is_impersonation=is_imp,
        )

    user_cliente = _coerce_cliente_uuid(user_cliente_id)
    if user_cliente is not None:
        return SessionClienteResolution(
            cliente_id=user_cliente,
            source="user_row",
            is_impersonation=is_imp,
        )

    raise AuthorizationError(
        detail="No se pudo resolver el tenant de la sesión.",
        internal_code="MISSING_SESSION_CLIENTE",
    )


def require_session_cliente_id(
    *,
    payload: Optional[Dict[str, Any]] = None,
    user_cliente_id: Optional[UUID] = None,
    request_cliente_id: Optional[UUID] = None,
    endpoint: Optional[str] = None,
) -> UUID:
    """Wrapper que resuelve cliente_id y emite log DEV [ORG-SESSION-SCOPE]."""
    resolution = resolve_session_cliente_id(
        payload=payload,
        user_cliente_id=user_cliente_id,
        request_cliente_id=request_cliente_id,
    )
    _log_org_session_scope(
        endpoint=endpoint,
        cliente_id=resolution.cliente_id,
        source=resolution.source,
        is_impersonation=resolution.is_impersonation,
        payload=payload,
    )
    return resolution.cliente_id


def resolve_org_scope_policy(*, resource: str) -> OrgScopePolicy:
    """
    Política de alcance por sub-recurso ORG.

    resource: empresa | sucursales | departamentos | cargos | centros_costo | parametros
    """
    key = (resource or "").strip().lower().replace("-", "_")
    if key in ("empresa",):
        return OrgScopePolicy.TENANT
    if key in ("parametros", "parametro"):
        return OrgScopePolicy.HYBRID
    return OrgScopePolicy.COMPANY


def require_company_scope_if_needed(
    *,
    policy: OrgScopePolicy,
    payload: Dict[str, Any],
    user_type: str,
    is_super_admin: bool = False,
    endpoint: Optional[str] = None,
) -> Optional[UUID]:
    """
    Etapa A — company / hybrid operativo exigen empresa en sesión salvo excepciones I1.

    Impersonación con empresa_selection_pending → 403 (solo /org/empresa permitido).
    """
    from app.core.tenant.company_scope import validate_erp_operational_session

    empresa_id = coerce_empresa_id(try_get_current_empresa_id()) or coerce_empresa_id(
        payload.get("empresa_id")
    )
    selection_pending = bool(payload.get("empresa_selection_pending"))
    is_imp = is_impersonation_payload(payload)

    _log_org_scope_policy(
        endpoint=endpoint,
        policy=policy,
        cliente_id=_coerce_cliente_uuid(payload.get("cliente_id")),
        empresa_id=empresa_id,
        is_impersonation=is_imp,
        empresa_selection_pending=selection_pending,
    )

    if policy == OrgScopePolicy.TENANT:
        return empresa_id

    if is_imp and selection_pending:
        raise AuthorizationError(
            detail="No hay empresa activa en la sesión. Seleccione una empresa antes de continuar.",
            internal_code="MISSING_SESSION_EMPRESA",
        )

    if policy in (OrgScopePolicy.COMPANY, OrgScopePolicy.HYBRID):
        return validate_erp_operational_session(
            payload=payload,
            user_type=user_type,
            is_super_admin=is_super_admin,
        )

    return empresa_id


def _log_org_session_scope(
    *,
    endpoint: Optional[str],
    cliente_id: UUID,
    source: str,
    is_impersonation: bool,
    payload: Optional[Dict[str, Any]],
) -> None:
    if settings.ENVIRONMENT != "development":
        return
    empresa_id = coerce_empresa_id((payload or {}).get("empresa_id"))
    logger.info(
        "[ORG-SESSION-SCOPE] endpoint=%s source=%s cliente_id=%s "
        "is_impersonation=%s empresa_id=%s empresa_selection_pending=%s",
        endpoint or "-",
        source,
        cliente_id,
        is_impersonation,
        empresa_id,
        bool((payload or {}).get("empresa_selection_pending")),
    )


def _log_org_scope_policy(
    *,
    endpoint: Optional[str],
    policy: OrgScopePolicy,
    cliente_id: Optional[UUID],
    empresa_id: Optional[UUID],
    is_impersonation: bool,
    empresa_selection_pending: bool,
) -> None:
    if settings.ENVIRONMENT != "development":
        return
    logger.info(
        "[ORG-SCOPE-POLICY] endpoint=%s scope_policy=%s cliente_id=%s "
        "empresa_id=%s is_impersonation=%s empresa_selection_pending=%s",
        endpoint or "-",
        policy.value,
        cliente_id,
        empresa_id,
        is_impersonation,
        empresa_selection_pending,
    )


def log_org_erp_session(
    *,
    endpoint: Optional[str],
    scope_kind: str,
    payload: Dict[str, Any],
    session_cliente_id: UUID,
) -> None:
    """Log DEV [ORG-ERP-SESSION] tras validación de dependencia de router."""
    if settings.ENVIRONMENT != "development":
        return
    logger.info(
        "[ORG-ERP-SESSION] endpoint=%s scope_kind=%s session_cliente_id=%s "
        "jwt_cliente_id=%s is_impersonation=%s empresa_selection_pending=%s "
        "empresa_id=%s",
        endpoint or "-",
        scope_kind,
        session_cliente_id,
        _coerce_cliente_uuid(payload.get("cliente_id")),
        is_impersonation_payload(payload),
        bool(payload.get("empresa_selection_pending")),
        coerce_empresa_id(payload.get("empresa_id")),
    )


def log_org_session_empresa(*, operation: str, empresa_id: UUID, resource: str) -> None:
    """Log DEV [ORG-SESSION-EMPRESA] — empresa activa usada en servicio ORG."""
    if settings.ENVIRONMENT != "development":
        return
    logger.info(
        "[ORG-SESSION-EMPRESA] operation=%s resource=%s empresa_id=%s",
        operation,
        resource,
        empresa_id,
    )


def log_org_company_scope(
    *,
    operation: str,
    client_id: Optional[UUID],
    session_empresa_id: UUID,
    resource: str,
    client_empresa_id: Optional[UUID] = None,
    source: Optional[str] = None,
) -> None:
    """Log DEV [ORG-COMPANY-SCOPE] — aislamiento company-scoped."""
    if settings.ENVIRONMENT != "development":
        return
    logger.info(
        "[ORG-COMPANY-SCOPE] operation=%s resource=%s client_id=%s "
        "session_empresa_id=%s client_empresa_id=%s source=%s",
        operation,
        resource,
        client_id,
        session_empresa_id,
        client_empresa_id,
        source,
    )


def log_org_tenant_scope(
    *,
    operation: str,
    client_id: UUID,
    resource: str = "empresa",
    empresa_id: Optional[UUID] = None,
) -> None:
    """Log DEV [ORG-TENANT-SCOPE] — operaciones tenant-wide (org_empresa)."""
    if settings.ENVIRONMENT != "development":
        return
    logger.info(
        "[ORG-TENANT-SCOPE] operation=%s resource=%s client_id=%s empresa_id=%s",
        operation,
        resource,
        client_id,
        empresa_id,
    )


def log_org_assert_tenant(
    *,
    resource: str,
    entity_id: UUID,
    session_client_id: UUID,
    row_cliente_id: Optional[UUID],
) -> None:
    """Log DEV [ORG-ASSERT-TENANT] — defensa cross-tenant post-query."""
    if settings.ENVIRONMENT != "development":
        return
    logger.info(
        "[ORG-ASSERT-TENANT] resource=%s entity_id=%s session_client_id=%s row_cliente_id=%s",
        resource,
        entity_id,
        session_client_id,
        row_cliente_id,
    )


def log_org_empresa_scope(
    *,
    operation: str,
    client_id: UUID,
    empresa_id: UUID,
) -> None:
    """Log DEV [ORG-EMPRESA-SCOPE] — CRUD/detalle org_empresa en tenant."""
    if settings.ENVIRONMENT != "development":
        return
    logger.info(
        "[ORG-EMPRESA-SCOPE] operation=%s client_id=%s empresa_id=%s",
        operation,
        client_id,
        empresa_id,
    )


def log_org_assert_empresa(
    *,
    resource: str,
    entity_id: UUID,
    session_empresa_id: UUID,
    row_empresa_id: Optional[UUID],
) -> None:
    """Log DEV [ORG-ASSERT-EMPRESA] — defensa en profundidad post-query."""
    if settings.ENVIRONMENT != "development":
        return
    logger.info(
        "[ORG-ASSERT-EMPRESA] resource=%s entity_id=%s session_empresa_id=%s row_empresa_id=%s",
        resource,
        entity_id,
        session_empresa_id,
        row_empresa_id,
    )


def log_org_hybrid_scope(
    *,
    operation: str,
    client_id: UUID,
    session_empresa_id: UUID,
    row_count: int = 0,
) -> None:
    """Log DEV [ORG-HYBRID-SCOPE] — lectura híbrida parámetros."""
    if settings.ENVIRONMENT != "development":
        return
    logger.info(
        "[ORG-HYBRID-SCOPE] operation=%s client_id=%s session_empresa_id=%s row_count=%s",
        operation,
        client_id,
        session_empresa_id,
        row_count,
    )


def log_org_param_precedence(
    *,
    merged_count: int,
    override_count: int,
    global_count: int,
) -> None:
    """Log DEV [ORG-PARAM-PRECEDENCE] — resultado merge global + override."""
    if settings.ENVIRONMENT != "development":
        return
    logger.info(
        "[ORG-PARAM-PRECEDENCE] merged=%s overrides_applied=%s globals_only=%s",
        merged_count,
        override_count,
        global_count,
    )


def log_org_param_global(*, operation: str, client_id: UUID) -> None:
    """Log DEV [ORG-PARAM-GLOBAL] — parámetro tenant-wide (empresa_id NULL)."""
    if settings.ENVIRONMENT != "development":
        return
    logger.info(
        "[ORG-PARAM-GLOBAL] operation=%s client_id=%s",
        operation,
        client_id,
    )


def log_org_param_empresa(
    *,
    operation: str,
    client_id: UUID,
    empresa_id: UUID,
) -> None:
    """Log DEV [ORG-PARAM-EMPRESA] — override por empresa."""
    if settings.ENVIRONMENT != "development":
        return
    logger.info(
        "[ORG-PARAM-EMPRESA] operation=%s client_id=%s empresa_id=%s",
        operation,
        client_id,
        empresa_id,
    )
