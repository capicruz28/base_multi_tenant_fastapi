"""
Aislamiento multi-empresa por sesión (JWT → empresa_context).

Blueprint ERP: toda operación company-scoped debe usar cliente_id + empresa_id de sesión + entity_id.
No usar query params ni body ajeno a la sesión para autorización de datos.

I1 — contrato sesión ERP operativa (require_erp_session):
  - Usuario autenticado, sin selection token.
  - empresa_id en JWT/ContextVar obligatorio salvo platform_admin documentado.

ORG Etapa A — políticas tenant/company/hybrid y cliente_id de sesión: ver session_scope.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import ColumnElement, and_

from app.core.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.tenant.empresa_context import coerce_empresa_id, try_get_current_empresa_id


def require_session_empresa_id() -> UUID:
    """
    Empresa activa del request (ContextVar, poblado desde JWT en deps).
    Raises AuthorizationError 403 si no hay empresa en sesión.
    """
    empresa_id = try_get_current_empresa_id()
    if empresa_id is None:
        raise AuthorizationError(
            detail="No hay empresa activa en la sesión. Seleccione una empresa antes de continuar.",
            internal_code="MISSING_SESSION_EMPRESA",
        )
    return empresa_id


def empresa_scoped_conditions(
    table: Any,
    *,
    client_id: UUID,
    empresa_id: UUID,
    entity_id_column: Any,
    entity_id: UUID,
) -> ColumnElement:
    """Condición SQL: cliente_id + empresa_id + clave de entidad."""
    return and_(
        table.c.cliente_id == client_id,
        table.c.empresa_id == empresa_id,
        entity_id_column == entity_id,
    )


def _coerce_cliente_id(value: Any) -> Optional[UUID]:
    """Normaliza cliente_id desde fila BD o parámetro."""
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


def tenant_empresa_scoped_conditions(
    table: Any,
    *,
    client_id: UUID,
    empresa_id: UUID,
) -> ColumnElement:
    """Condición SQL tenant-scoped org_empresa: cliente_id + empresa_id."""
    return and_(
        table.c.cliente_id == client_id,
        table.c.empresa_id == empresa_id,
    )


def assert_row_tenant(
    row: Optional[Dict[str, Any]],
    client_id: UUID,
    *,
    not_found_detail: str = "Recurso no encontrado",
) -> None:
    """
    Defensa en profundidad: fila debe pertenecer al tenant de sesión (cliente_id).
    Cross-tenant → NotFoundError (404), no 403.
    """
    if row is None:
        raise NotFoundError(detail=not_found_detail)
    row_cliente = _coerce_cliente_id(row.get("cliente_id"))
    if row_cliente != client_id:
        raise NotFoundError(detail=not_found_detail)


def assert_row_empresa(
    row: Optional[Dict[str, Any]],
    empresa_id: UUID,
    *,
    not_found_detail: str = "Recurso no encontrado",
) -> None:
    """
    Defensa en profundidad: fila debe pertenecer a la empresa de sesión.
    Cross-company → NotFoundError (404), no 403.
    """
    if row is None:
        raise NotFoundError(detail=not_found_detail)
    row_empresa = coerce_empresa_id(row.get("empresa_id"))
    if row_empresa != empresa_id:
        raise NotFoundError(detail=not_found_detail)


def enforce_body_empresa_matches_session(body_empresa_id: UUID) -> UUID:
    """
    Valida que empresa_id del body coincida con la sesión.
    Mismatch → AuthorizationError 403 EMPRESA_MISMATCH.
    """
    session_empresa = require_session_empresa_id()
    body_empresa = coerce_empresa_id(body_empresa_id)
    if body_empresa is None or body_empresa != session_empresa:
        raise AuthorizationError(
            detail="empresa_id del cuerpo no coincide con la empresa activa de la sesión.",
            internal_code="EMPRESA_MISMATCH",
        )
    return session_empresa


def reject_client_empresa_override(
    client_empresa_id: Optional[UUID],
    *,
    source: str = "solicitud",
) -> None:
    """
    Rechaza empresa_id explícito del cliente (query/header) distinto a la sesión.
    """
    if client_empresa_id is None:
        return
    session_empresa = require_session_empresa_id()
    client_empresa = coerce_empresa_id(client_empresa_id)
    if client_empresa is not None and client_empresa != session_empresa:
        raise AuthorizationError(
            detail=f"empresa_id de {source} no coincide con la empresa activa de la sesión.",
            internal_code="EMPRESA_MISMATCH",
        )


def reject_client_empresa_scope_override(
    client_empresa_id: Optional[UUID],
    *,
    source: str = "solicitud",
) -> None:
    """
    ORG Etapa B — rechaza empresa_id de query/body distinto a la sesión ERP.

    Mismo criterio que reject_client_empresa_override; código interno específico ORG.
    """
    if client_empresa_id is None:
        return
    session_empresa = require_session_empresa_id()
    client_empresa = coerce_empresa_id(client_empresa_id)
    if client_empresa is not None and client_empresa != session_empresa:
        from app.core.tenant.session_scope import log_org_company_scope

        log_org_company_scope(
            operation="reject_override",
            client_id=None,
            session_empresa_id=session_empresa,
            client_empresa_id=client_empresa,
            source=source,
            resource="org_company",
        )
        raise AuthorizationError(
            detail=f"empresa_id de {source} no coincide con la empresa activa de la sesión.",
            internal_code="EMPRESA_SCOPE_MISMATCH",
        )


async def ensure_empresa_in_tenant(client_id: UUID, empresa_id: UUID) -> None:
    """Verifica que la empresa pertenezca al tenant (org_empresa)."""
    from app.modules.org.application.services.empresa_service import get_empresa_servicio

    await get_empresa_servicio(client_id=client_id, empresa_id=empresa_id)


def is_platform_operator(
    *,
    payload: Optional[Dict[str, Any]] = None,
    user_type: Optional[str] = None,
    is_super_admin: bool = False,
) -> bool:
    """
    Operador de plataforma (sin empresa operativa obligatoria en sesión ERP).

    Incluye user_type=platform_admin y superadmin cross-tenant (claim es_superadmin).
    No confundir con tenant_admin ni SUPER_ADMIN solo del tenant destino.
    """
    if (payload or {}).get("is_impersonation"):
        return False

    ut = (user_type or (payload or {}).get("user_type") or "").lower()
    if ut == "platform_admin":
        return True
    if is_super_admin and (payload or {}).get("es_superadmin"):
        return True
    return False


def resolve_empresa_id_for_rbac(
    *,
    payload: Optional[Dict[str, Any]] = None,
) -> Optional[UUID]:
    """
    Empresa activa para Permission Resolver / menú.
    Prioridad: ContextVar (I0) > claim JWT en payload.
    """
    if payload is not None:
        from_jwt = coerce_empresa_id(payload.get("empresa_id"))
        ctx = try_get_current_empresa_id()
        if ctx is not None:
            return ctx
        return from_jwt
    return try_get_current_empresa_id()


def validate_erp_operational_session(
    *,
    payload: Dict[str, Any],
    user_type: str,
    is_super_admin: bool = False,
) -> Optional[UUID]:
    """
    Valida contrato I1 para rutas ERP operativas.

    Returns:
        empresa_id de sesión si aplica; None solo para platform_operator sin empresa.

    Raises:
        AuthorizationError 403 si falta empresa en usuarios ERP normales.
    """
    empresa_id = resolve_empresa_id_for_rbac(payload=payload)
    if empresa_id is not None:
        return empresa_id
    if (payload or {}).get("is_impersonation"):
        return None
    if is_platform_operator(
        payload=payload,
        user_type=user_type,
        is_super_admin=is_super_admin,
    ):
        return None
    raise AuthorizationError(
        detail="No hay empresa activa en la sesión. Seleccione una empresa antes de continuar.",
        internal_code="MISSING_SESSION_EMPRESA",
    )


@dataclass(frozen=True)
class RoleAssignTarget:
    """Alcance objetivo de una asignación usuario_rol (I2.2)."""

    empresa_id: Optional[UUID]
    is_global: bool


@dataclass(frozen=True)
class RoleListScope:
    """
    Alcance para lecturas/revoke de usuario_rol (I2.3).

    tenant_wide=True: platform_admin ve todas las asignaciones del tenant.
    tenant_wide=False: solo globales + empresa_id de sesión.
    """

    tenant_wide: bool
    empresa_id: Optional[UUID] = None


def assignment_scope_matches(
    existing_empresa_id: Any,
    target_empresa_id: Optional[UUID],
) -> bool:
    """True si el scope almacenado coincide con el objetivo (NULL = global)."""
    return coerce_empresa_id(existing_empresa_id) == coerce_empresa_id(target_empresa_id)


async def resolve_role_assign_target(
    *,
    cliente_id: UUID,
    body_empresa_id: Optional[UUID] = None,
    scope_global: bool = False,
    payload: Optional[Dict[str, Any]] = None,
    user_type: Optional[str] = None,
    is_super_admin: bool = False,
) -> RoleAssignTarget:
    """
    Resuelve empresa_id objetivo para POST assign role.

    - Tenant admin: empresa de sesión obligatoria; no puede asignar global.
    - platform_admin: global explícito (scope_global) o empresa_id en body validada en tenant.
  """
    platform = is_platform_operator(
        payload=payload,
        user_type=user_type,
        is_super_admin=is_super_admin,
    )

    if scope_global and body_empresa_id is not None:
        raise ValidationError(
            detail="No puede indicar empresa_id y scope_global a la vez.",
            internal_code="ROLE_ASSIGN_SCOPE_CONFLICT",
        )

    if scope_global:
        if not platform:
            raise AuthorizationError(
                detail="Solo un operador de plataforma puede asignar roles globales al tenant.",
                internal_code="GLOBAL_ASSIGN_FORBIDDEN",
            )
        return RoleAssignTarget(empresa_id=None, is_global=True)

    if body_empresa_id is not None:
        target = coerce_empresa_id(body_empresa_id)
        if target is None:
            if not platform:
                raise AuthorizationError(
                    detail="Solo un operador de plataforma puede asignar roles globales al tenant.",
                    internal_code="GLOBAL_ASSIGN_FORBIDDEN",
                )
            return RoleAssignTarget(empresa_id=None, is_global=True)
        await ensure_empresa_in_tenant(client_id, target)
        if not platform:
            session_empresa = resolve_empresa_id_for_rbac(payload=payload)
            if session_empresa is None:
                raise AuthorizationError(
                    detail="No hay empresa activa en la sesión. Seleccione una empresa antes de continuar.",
                    internal_code="MISSING_SESSION_EMPRESA",
                )
            if target != session_empresa:
                raise AuthorizationError(
                    detail="empresa_id del cuerpo no coincide con la empresa activa de la sesión.",
                    internal_code="EMPRESA_MISMATCH",
                )
        return RoleAssignTarget(empresa_id=target, is_global=False)

    session_empresa = resolve_empresa_id_for_rbac(payload=payload)
    if session_empresa is not None:
        return RoleAssignTarget(empresa_id=session_empresa, is_global=False)

    if platform:
        raise ValidationError(
            detail=(
                "Indique scope_global=true para asignación global o empresa_id en el cuerpo "
                "para asignación por empresa."
            ),
            internal_code="ROLE_ASSIGN_SCOPE_REQUIRED",
        )

    raise AuthorizationError(
        detail="No hay empresa activa en la sesión. Seleccione una empresa antes de continuar.",
        internal_code="MISSING_SESSION_EMPRESA",
    )


async def resolve_role_list_scope(
    *,
    payload: Optional[Dict[str, Any]] = None,
    user_type: Optional[str] = None,
    is_super_admin: bool = False,
) -> RoleListScope:
    """
    Scope para GET roles admin, /me y DELETE revoke (simétrico a assign en tenant/platform).

    - platform_admin: todas las asignaciones del tenant (con asignacion_empresa_id).
    - tenant ERP: empresa activa obligatoria; filtro NULL | empresa_id.
    """
    if is_platform_operator(
        payload=payload,
        user_type=user_type,
        is_super_admin=is_super_admin,
    ):
        return RoleListScope(tenant_wide=True, empresa_id=None)

    empresa_id = resolve_empresa_id_for_rbac(payload=payload)
    if empresa_id is None:
        raise AuthorizationError(
            detail="No hay empresa activa en la sesión. Seleccione una empresa antes de continuar.",
            internal_code="MISSING_SESSION_EMPRESA",
        )
    return RoleListScope(tenant_wide=False, empresa_id=empresa_id)


def assert_assignment_visible_in_scope(
    existing_empresa_id: Any,
    scope: RoleListScope,
    *,
    operation: str = "revoke",
) -> None:
    """
    Valida que la fila usuario_rol sea visible en el scope actual.

    Revoke cross-empresa → NotFoundError (404 INV).
    Revoke global por tenant → ConflictError 409.
    """
    if scope.tenant_wide:
        return

    existing = coerce_empresa_id(existing_empresa_id)
    session_empresa = scope.empresa_id

    if existing is None:
        raise ConflictError(
            detail=(
                "El rol está asignado de forma global al tenant. "
                "Solo un operador de plataforma puede revocarlo."
            ),
            internal_code="ROLE_REVOKE_GLOBAL",
        )

    if session_empresa is not None and existing != session_empresa:
        raise NotFoundError(
            detail=(
                f"No existe asignación entre el usuario y el rol para esta operación de {operation}."
            ),
            internal_code="ASSIGNMENT_NOT_FOUND",
        )


# Re-exports ORG Etapa A/C1 (INV no depende de estos símbolos).
from app.core.tenant.session_scope import (  # noqa: E402,F401
    OrgScopePolicy,
    SessionClienteResolution,
    require_company_scope_if_needed as org_require_company_scope_if_needed,
    require_session_cliente_id,
    resolve_org_scope_policy,
    resolve_session_cliente_id,
)

__all__ = [
    "assert_row_tenant",
    "tenant_empresa_scoped_conditions",
    "assert_row_empresa",
    "require_session_empresa_id",
    "ensure_empresa_in_tenant",
]
