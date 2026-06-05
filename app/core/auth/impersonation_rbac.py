"""
RBAC efectivo durante impersonación (scope tenant, sin usuario_rol local).

El operador platform actúa como tenant_admin del cliente impersonado usando
los permisos del rol ADMIN_TENANT del tenant, filtrados por cliente_modulo.
"""
from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import text

from app.core.auth.impersonation import is_impersonation_payload
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_query

logger = logging.getLogger(__name__)

# Mismo filtro que permisos_usuario_service (módulos contratados + permisos globales).
_CLIENTE_MODULO_FILTER = """
      AND (
          p.modulo_id IS NULL
          OR EXISTS (
              SELECT 1 FROM cliente_modulo cm
              WHERE cm.modulo_id = p.modulo_id
                AND cm.cliente_id = :cliente_id
                AND cm.esta_activo = 1
                AND (cm.fecha_vencimiento IS NULL OR cm.fecha_vencimiento > CAST(GETDATE() AS DATE))
          )
      )
"""

_impersonation_permissions_ctx: ContextVar[Optional[frozenset[str]]] = ContextVar(
    "impersonation_effective_permissions", default=None
)


def is_impersonation_effective_tenant_session(
    payload: Optional[Dict[str, Any]],
) -> bool:
    if not is_impersonation_payload(payload):
        return False
    scope = (payload or {}).get("effective_scope") or "tenant"
    return str(scope).lower() == "tenant"


def resolve_impersonation_tenant_cliente_id(
    payload: Optional[Dict[str, Any]],
    *,
    user_cliente_id: Optional[UUID] = None,
    request_cliente_id: Optional[UUID] = None,
) -> UUID:
    """
    cliente_id del tenant impersonado para RBAC (permisos, menú, ORG).

    Prioridad alineada con ORG session_scope: JWT ``cliente_id`` del token de
    impersonación, no ``current_user.cliente_id`` (operador SYSTEM) ni el tenant
    del host platform en ``request_cliente_id``.
    """
    from app.core.tenant.session_scope import resolve_session_cliente_id

    if not is_impersonation_effective_tenant_session(payload):
        raise ValueError(
            "resolve_impersonation_tenant_cliente_id requiere sesión de impersonación tenant"
        )

    resolution = resolve_session_cliente_id(
        payload=payload,
        user_cliente_id=user_cliente_id,
        request_cliente_id=request_cliente_id,
    )
    if resolution.source != "jwt_impersonation":
        logger.warning(
            "[IMPERSONATION-RBAC] tenant cliente_id vía %s (esperado jwt_impersonation); "
            "cliente_id=%s",
            resolution.source,
            resolution.cliente_id,
        )
    return resolution.cliente_id


def get_impersonation_effective_permissions_cached() -> Optional[frozenset[str]]:
    return _impersonation_permissions_ctx.get()


def clear_impersonation_rbac_context() -> None:
    _impersonation_permissions_ctx.set(None)


def impersonation_passes_tenant_admin_gate(user: Any) -> bool:
    """RoleChecker 'Administrador': sesión impersonación con nivel tenant_admin efectivo."""
    if get_impersonation_effective_permissions_cached() is None:
        return False
    return int(getattr(user, "access_level", 0) or 0) >= 4


async def get_effective_impersonation_permissions(
    cliente_id: UUID,
    *,
    database_type: str = "single",
) -> List[str]:
    """
    Permisos equivalentes a tenant_admin en el tenant impersonado.

    Fuente: rol_permiso del rol ADMIN_TENANT (o nombre Administrador) del cliente,
    filtrado por módulos activos en cliente_modulo. Sin usuario_rol del operador.
    """
    if database_type == "multi":
        codes = await _impersonation_permisos_dedicated(cliente_id)
    else:
        codes = await _impersonation_permisos_single(cliente_id)

    logger.info(
        "[IMPERSONATION-RBAC] effective_permissions=%s source=impersonation_effective_admin "
        "cliente_id=%s count=%s",
        codes[:20] if len(codes) > 20 else codes,
        cliente_id,
        len(codes),
    )
    if len(codes) > 20:
        logger.info(
            "[IMPERSONATION-RBAC] ... y %s permisos más",
            len(codes) - 20,
        )
    return codes


async def _impersonation_permisos_single(cliente_id: UUID) -> List[str]:
    sql = text(
        """
        SELECT DISTINCT p.codigo
        FROM rol r
        INNER JOIN rol_permiso rp
            ON rp.rol_id = r.rol_id AND rp.cliente_id = :cliente_id
        INNER JOIN permiso p ON p.permiso_id = rp.permiso_id AND p.es_activo = 1
        WHERE r.cliente_id = :cliente_id
          AND r.es_activo = 1
          AND (r.codigo_rol = N'ADMIN_TENANT' OR r.nombre = N'Administrador')
        """
        + _CLIENTE_MODULO_FILTER
        + "\n"
    ).bindparams(cliente_id=cliente_id)

    rows = await execute_query(
        sql,
        client_id=cliente_id,
        connection_type=DatabaseConnection.DEFAULT,
    )
    return [r["codigo"] for r in rows if r.get("codigo")]


async def _impersonation_permisos_dedicated(cliente_id: UUID) -> List[str]:
    sql_ids = text(
        """
        SELECT DISTINCT rp.permiso_id
        FROM rol r
        INNER JOIN rol_permiso rp
            ON rp.rol_id = r.rol_id AND rp.cliente_id = :cliente_id
        WHERE r.cliente_id = :cliente_id
          AND r.es_activo = 1
          AND (r.codigo_rol = N'ADMIN_TENANT' OR r.nombre = N'Administrador')
        """
    ).bindparams(cliente_id=cliente_id)

    rows_ids = await execute_query(
        sql_ids,
        client_id=cliente_id,
        connection_type=DatabaseConnection.DEFAULT,
    )
    if not rows_ids:
        return []

    permiso_ids = [r["permiso_id"] for r in rows_ids if r.get("permiso_id")]
    if not permiso_ids:
        return []

    placeholders = ", ".join(f":p{i}" for i in range(len(permiso_ids)))
    params = {f"p{i}": pid for i, pid in enumerate(permiso_ids)}
    params["cliente_id"] = cliente_id

    sql_codigos = text(
        f"""
        SELECT codigo FROM permiso p
        WHERE p.es_activo = 1 AND p.permiso_id IN ({placeholders})
        """
        + _CLIENTE_MODULO_FILTER
        + "\n"
    ).bindparams(**params)

    rows = await execute_query(
        sql_codigos,
        connection_type=DatabaseConnection.ADMIN,
    )
    return [r["codigo"] for r in rows if r.get("codigo")]


async def apply_impersonation_effective_permissions_to_user(
    user: Any,
    *,
    cliente_id: UUID,
    database_type: str = "single",
    payload: Optional[Dict[str, Any]] = None,
    request_cliente_id: Optional[UUID] = None,
) -> List[str]:
    """Carga permisos impersonados en el usuario y ContextVar del request."""
    if payload is not None and is_impersonation_effective_tenant_session(payload):
        cliente_id = resolve_impersonation_tenant_cliente_id(
            payload,
            user_cliente_id=cliente_id,
            request_cliente_id=request_cliente_id,
        )
    codes = await get_effective_impersonation_permissions(
        cliente_id, database_type=database_type
    )
    _impersonation_permissions_ctx.set(frozenset(codes))
    if hasattr(user, "permisos"):
        user.permisos = codes
    return codes


def resolve_menu_cliente_id_for_session(
    *,
    payload: Optional[Dict[str, Any]],
    user_cliente_id: Optional[UUID],
    request_cliente_id: Optional[UUID] = None,
) -> Optional[UUID]:
    """
    cliente_id para /auth/menu: JWT tenant en impersonación; legacy fuera de ella.
    """
    try:
        if is_impersonation_effective_tenant_session(payload):
            return resolve_impersonation_tenant_cliente_id(
                payload,
                user_cliente_id=user_cliente_id,
                request_cliente_id=request_cliente_id,
            )
        from app.core.tenant.session_scope import resolve_session_cliente_id

        resolution = resolve_session_cliente_id(
            payload=payload,
            user_cliente_id=user_cliente_id,
            request_cliente_id=request_cliente_id,
        )
        return resolution.cliente_id
    except Exception:
        return user_cliente_id or request_cliente_id


def _module_code_prefixes_from_permissions(
    permission_codes: List[str],
) -> set[str]:
    """Prefijos de permiso (org, inv) alineados a modulo.codigo (ORG, INV)."""
    prefixes: set[str] = set()
    for code in permission_codes:
        if not code or "." not in code:
            continue
        prefixes.add(code.split(".", 1)[0].strip().lower())
    return prefixes


def filter_menu_by_impersonation_permissions(
    menu: Any,
    permission_codes: List[str],
) -> Any:
    """
    Tras cliente_modulo: deja solo módulos con al menos un prefijo de permiso efectivo.
    Evita menú tenant_admin elevado con módulos sin permiso impersonado.
    """
    from app.modules.modulos.presentation.schemas import MenuUsuarioResponse

    prefixes = _module_code_prefixes_from_permissions(permission_codes)
    if not prefixes:
        return MenuUsuarioResponse(modulos=[])

    kept = [
        m
        for m in (menu.modulos or [])
        if (getattr(m, "codigo", None) or "").strip().lower() in prefixes
    ]
    return MenuUsuarioResponse(modulos=kept)
