"""F6-P1 — Identity Gateway: lookup y update mínimo para login."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.identity.identity_context import IdentityContext
from app.core.identity.identity_scope import IdentityScope
from app.core.tenant.context import try_get_tenant_context
from app.infrastructure.identity.identity_query_executor import (
    execute_identity_query,
    execute_identity_update,
    execute_platform_identity_query,
)
from app.infrastructure.identity.queries.auth_runtime_identity_queries import (
    select_admin_tenant_wide_count_engine_scoped,
    select_admin_tenant_wide_count_row_scoped,
    select_distinct_empresa_ids_engine_scoped,
    select_distinct_empresa_ids_row_scoped,
    select_user_password_policy_engine_scoped,
    select_user_password_policy_row_scoped,
    select_user_role_names_engine_scoped,
    select_user_role_names_row_scoped,
    select_user_roles_for_auth_engine_scoped,
    select_user_roles_for_auth_row_scoped,
    text_admin_cliente_count_engine_scoped,
    text_admin_cliente_count_row_scoped,
    text_platform_superadmin_count,
    text_user_empresa_default_engine_scoped,
    text_user_empresa_default_row_scoped,
)
from app.infrastructure.identity.queries.user_identity_queries import (
    search_user_ids_engine_scoped,
    search_user_ids_row_scoped,
    select_user_access_level_engine_scoped,
    select_user_access_level_row_scoped,
    select_user_by_username_engine_scoped,
    select_user_by_username_row_scoped,
    select_users_by_ids_engine_scoped,
    select_users_by_ids_row_scoped,
    update_user_last_access,
)

logger = logging.getLogger(__name__)

_NULL_CLIENTE_UUID = UUID("00000000-0000-0000-0000-000000000000")


class IdentityGateway:
    """Punto único de acceso al Identity Store para login (F6-P1)."""

    @staticmethod
    def resolve_identity_scope() -> IdentityScope:
        """Dedicated (multi) → ENGINE_SCOPED; Shared → ROW_SCOPED."""
        tenant_context = try_get_tenant_context()
        if tenant_context and tenant_context.database_type == "multi":
            return IdentityScope.ENGINE_SCOPED
        return IdentityScope.ROW_SCOPED

    @staticmethod
    async def get_user_by_username(
        ctx: IdentityContext,
        username: str,
    ) -> Optional[Dict[str, Any]]:
        scope = IdentityGateway.resolve_identity_scope()
        if scope == IdentityScope.ENGINE_SCOPED:
            query = select_user_by_username_engine_scoped(username=username)
            logger.debug(
                "[IDENTITY] ENGINE_SCOPED login lookup username=%r cliente=%s",
                username,
                ctx.cliente_id,
            )
        else:
            query = select_user_by_username_row_scoped(
                cliente_id=ctx.cliente_id,
                username=username,
            )
            logger.debug(
                "[IDENTITY] ROW_SCOPED login lookup username=%r cliente=%s",
                username,
                ctx.cliente_id,
            )

        rows = await execute_identity_query(
            query,
            cliente_id=ctx.cliente_id,
            identity_scope=scope,
        )
        return rows[0] if rows else None

    @staticmethod
    async def get_platform_user_by_username(
        username: str,
        *,
        platform_cliente_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Superadmin: CP (ADMIN) con filtro explícito por cliente SYSTEM."""
        query = select_user_by_username_row_scoped(
            cliente_id=platform_cliente_id,
            username=username,
        )
        rows = await execute_platform_identity_query(
            query,
            platform_cliente_id=platform_cliente_id,
        )
        return rows[0] if rows else None

    @staticmethod
    def normalize_user_cliente_id(
        user: Dict[str, Any],
        ctx: IdentityContext,
    ) -> Dict[str, Any]:
        """Dedicated: reemplaza cliente_id NULL/nulo por el del contexto tenant."""
        if IdentityGateway.resolve_identity_scope() != IdentityScope.ENGINE_SCOPED:
            return user

        user_cliente_id = user.get("cliente_id")
        if user_cliente_id:
            if isinstance(user_cliente_id, str):
                try:
                    user_cliente_id = UUID(user_cliente_id)
                except (ValueError, AttributeError):
                    user_cliente_id = None
            elif not isinstance(user_cliente_id, UUID):
                user_cliente_id = None

        if not user_cliente_id or user_cliente_id == _NULL_CLIENTE_UUID:
            user["cliente_id"] = ctx.cliente_id
            logger.debug(
                "[IDENTITY] ENGINE_SCOPED: cliente_id normalizado a %s",
                ctx.cliente_id,
            )
        else:
            user["cliente_id"] = user_cliente_id
        return user

    @staticmethod
    async def update_last_access(
        ctx: IdentityContext,
        usuario_id: UUID,
    ) -> None:
        scope = IdentityGateway.resolve_identity_scope()
        query = update_user_last_access(usuario_id=usuario_id)
        await execute_identity_update(
            query,
            cliente_id=ctx.cliente_id,
            identity_scope=scope,
        )

    @staticmethod
    def _map_access_level_row(level_data: Dict[str, Any]) -> Dict[str, Any]:
        access_level = int(level_data.get("max_level") or 1)
        super_admin_count = level_data.get("super_admin_count") or 0
        is_super_admin = int(super_admin_count) > 0
        if is_super_admin:
            user_type = "platform_admin"
        elif access_level >= 4:
            user_type = "tenant_admin"
        else:
            user_type = "user"
        return {
            "access_level": access_level,
            "is_super_admin": is_super_admin,
            "user_type": user_type,
        }

    @staticmethod
    async def get_user_access_level_info(
        ctx: IdentityContext,
        usuario_id: UUID,
        *,
        empresa_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """LBAC desde usuario_rol + rol (Identity Store, F6-P2a)."""
        from app.core.tenant.empresa_context import resolve_empresa_id

        resolved_empresa_id = resolve_empresa_id(empresa_id)
        scope = IdentityGateway.resolve_identity_scope()

        if scope == IdentityScope.ENGINE_SCOPED:
            query = select_user_access_level_engine_scoped(
                usuario_id=usuario_id,
                empresa_id=resolved_empresa_id,
            )
            logger.debug(
                "[IDENTITY] ENGINE_SCOPED access level usuario=%s cliente=%s",
                usuario_id,
                ctx.cliente_id,
            )
        else:
            query = select_user_access_level_row_scoped(
                usuario_id=usuario_id,
                cliente_id=ctx.cliente_id,
                empresa_id=resolved_empresa_id,
            )
            logger.debug(
                "[IDENTITY] ROW_SCOPED access level usuario=%s cliente=%s",
                usuario_id,
                ctx.cliente_id,
            )

        rows = await execute_identity_query(
            query,
            cliente_id=ctx.cliente_id,
            identity_scope=scope,
        )
        if rows:
            info = IdentityGateway._map_access_level_row(rows[0])
            logger.debug(
                "Niveles calculados - Usuario %s: level=%s, super_admin=%s, type=%s",
                usuario_id,
                info["access_level"],
                info["is_super_admin"],
                info["user_type"],
            )
            return info

        logger.warning(
            "No se pudieron calcular niveles para usuario %s, usando valores por defecto",
            usuario_id,
        )
        return {
            "access_level": 1,
            "is_super_admin": False,
            "user_type": "user",
        }

    @staticmethod
    async def get_users_by_ids(
        ctx: IdentityContext,
        usuario_ids: List[UUID],
    ) -> Dict[UUID, Dict[str, Any]]:
        """Batch lookup de campos de display del usuario (F6-P4 read layer)."""
        if not usuario_ids:
            return {}

        unique_ids = list({uid for uid in usuario_ids if uid})
        scope = IdentityGateway.resolve_identity_scope()
        if scope == IdentityScope.ENGINE_SCOPED:
            query = select_users_by_ids_engine_scoped(usuario_ids=unique_ids)
        else:
            query = select_users_by_ids_row_scoped(
                cliente_id=ctx.cliente_id,
                usuario_ids=unique_ids,
            )

        rows = await execute_identity_query(
            query,
            cliente_id=ctx.cliente_id,
            identity_scope=scope,
        )
        result: Dict[UUID, Dict[str, Any]] = {}
        for row in rows:
            uid = row.get("usuario_id")
            if not uid:
                continue
            if isinstance(uid, str):
                uid = UUID(uid)
            result[uid] = {
                "nombre_usuario": row.get("nombre_usuario"),
                "nombre": row.get("nombre"),
                "apellido": row.get("apellido"),
            }
        return result

    @staticmethod
    async def search_user_ids(
        ctx: IdentityContext,
        search: str,
    ) -> List[UUID]:
        """IDs de usuarios cuyo nombre/username/apellido coincide con search."""
        if not search or not search.strip():
            return []

        scope = IdentityGateway.resolve_identity_scope()
        if scope == IdentityScope.ENGINE_SCOPED:
            query = search_user_ids_engine_scoped(search=search.strip())
        else:
            query = search_user_ids_row_scoped(
                cliente_id=ctx.cliente_id,
                search=search.strip(),
            )

        rows = await execute_identity_query(
            query,
            cliente_id=ctx.cliente_id,
            identity_scope=scope,
        )
        ids: List[UUID] = []
        for row in rows:
            uid = row.get("usuario_id")
            if not uid:
                continue
            if isinstance(uid, str):
                uid = UUID(uid)
            ids.append(uid)
        return ids

    @staticmethod
    async def get_user_for_refresh(
        ctx: IdentityContext,
        username: str,
        *,
        is_platform: bool = False,
        platform_cliente_id: Optional[UUID] = None,
    ) -> Optional[Dict[str, Any]]:
        """Carga usuario para refresh token (F8-A)."""
        if is_platform:
            if not platform_cliente_id:
                return None
            user = await IdentityGateway.get_platform_user_by_username(
                username,
                platform_cliente_id=platform_cliente_id,
            )
            return user

        user = await IdentityGateway.get_user_by_username(ctx, username)
        if user:
            user = IdentityGateway.normalize_user_cliente_id(user, ctx)
        return user

    @staticmethod
    async def get_user_password_policy_fields(
        ctx: IdentityContext,
        usuario_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        scope = IdentityGateway.resolve_identity_scope()
        if scope == IdentityScope.ENGINE_SCOPED:
            query = select_user_password_policy_engine_scoped(usuario_id=usuario_id)
        else:
            query = select_user_password_policy_row_scoped(
                usuario_id=usuario_id,
                cliente_id=ctx.cliente_id,
            )
        rows = await execute_identity_query(
            query,
            cliente_id=ctx.cliente_id,
            identity_scope=scope,
        )
        return rows[0] if rows else None

    @staticmethod
    async def get_user_empresa_default_id(
        ctx: IdentityContext,
        usuario_id: UUID,
    ) -> Optional[UUID]:
        scope = IdentityGateway.resolve_identity_scope()
        if scope == IdentityScope.ENGINE_SCOPED:
            query = text_user_empresa_default_engine_scoped(usuario_id=usuario_id)
        else:
            query = text_user_empresa_default_row_scoped(
                usuario_id=usuario_id,
                cliente_id=ctx.cliente_id,
            )
        rows = await execute_identity_query(
            query,
            cliente_id=ctx.cliente_id,
            identity_scope=scope,
        )
        if not rows:
            return None
        raw = rows[0].get("empresa_default_id")
        if not raw:
            return None
        if isinstance(raw, UUID):
            return raw
        try:
            return UUID(str(raw))
        except (ValueError, TypeError):
            return None

    @staticmethod
    async def get_user_eligible_empresa_ids(
        ctx: IdentityContext,
        usuario_id: UUID,
    ) -> List[UUID]:
        scope = IdentityGateway.resolve_identity_scope()
        if scope == IdentityScope.ENGINE_SCOPED:
            query = select_distinct_empresa_ids_engine_scoped(usuario_id=usuario_id)
        else:
            query = select_distinct_empresa_ids_row_scoped(
                usuario_id=usuario_id,
                cliente_id=ctx.cliente_id,
            )
        rows = await execute_identity_query(
            query,
            cliente_id=ctx.cliente_id,
            identity_scope=scope,
        )
        ids: List[UUID] = []
        for row in rows:
            eid = row.get("empresa_id")
            if not eid:
                continue
            if isinstance(eid, str):
                eid = UUID(eid)
            ids.append(eid)
        return ids

    @staticmethod
    async def is_admin_tenant_wide(
        ctx: IdentityContext,
        usuario_id: UUID,
    ) -> bool:
        scope = IdentityGateway.resolve_identity_scope()
        if scope == IdentityScope.ENGINE_SCOPED:
            query = select_admin_tenant_wide_count_engine_scoped(usuario_id=usuario_id)
        else:
            query = select_admin_tenant_wide_count_row_scoped(
                usuario_id=usuario_id,
                cliente_id=ctx.cliente_id,
            )
        rows = await execute_identity_query(
            query,
            cliente_id=ctx.cliente_id,
            identity_scope=scope,
        )
        if not rows:
            return False
        count_key = "admin_sin_empresa_count"
        if count_key not in rows[0] and len(rows[0]) == 1:
            return int(list(rows[0].values())[0] or 0) > 0
        return int(rows[0].get(count_key) or 0) > 0

    @staticmethod
    async def is_admin_cliente(
        ctx: IdentityContext,
        usuario_id: UUID,
        *,
        empresa_id: Optional[UUID] = None,
    ) -> bool:
        from app.core.tenant.empresa_context import resolve_empresa_id

        resolved_empresa_id = resolve_empresa_id(empresa_id)
        scope = IdentityGateway.resolve_identity_scope()
        if scope == IdentityScope.ENGINE_SCOPED:
            query = text_admin_cliente_count_engine_scoped(
                usuario_id=usuario_id,
                empresa_id=resolved_empresa_id,
            )
        else:
            query = text_admin_cliente_count_row_scoped(
                usuario_id=usuario_id,
                cliente_id=ctx.cliente_id,
                empresa_id=resolved_empresa_id,
            )
        rows = await execute_identity_query(
            query,
            cliente_id=ctx.cliente_id,
            identity_scope=scope,
        )
        if not rows:
            return False
        return int(rows[0].get("admin_cliente_count") or 0) > 0

    @staticmethod
    async def get_user_role_names(
        ctx: IdentityContext,
        usuario_id: UUID,
        *,
        empresa_id: Optional[UUID] = None,
    ) -> List[str]:
        from app.core.tenant.empresa_context import resolve_empresa_id

        resolved_empresa_id = resolve_empresa_id(empresa_id)
        scope = IdentityGateway.resolve_identity_scope()
        if scope == IdentityScope.ENGINE_SCOPED:
            query = select_user_role_names_engine_scoped(
                usuario_id=usuario_id,
                empresa_id=resolved_empresa_id,
            )
        else:
            query = select_user_role_names_row_scoped(
                usuario_id=usuario_id,
                cliente_id=ctx.cliente_id,
                empresa_id=resolved_empresa_id,
            )
        rows = await execute_identity_query(
            query,
            cliente_id=ctx.cliente_id,
            identity_scope=scope,
        )
        return [str(row["nombre"]) for row in rows if row.get("nombre")]

    @staticmethod
    async def get_user_roles_for_auth(
        ctx: IdentityContext,
        usuario_id: UUID,
        *,
        empresa_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        from app.core.tenant.empresa_context import resolve_empresa_id

        resolved_empresa_id = resolve_empresa_id(empresa_id)
        scope = IdentityGateway.resolve_identity_scope()
        if scope == IdentityScope.ENGINE_SCOPED:
            query = select_user_roles_for_auth_engine_scoped(
                usuario_id=usuario_id,
                empresa_id=resolved_empresa_id,
            )
        else:
            query = select_user_roles_for_auth_row_scoped(
                usuario_id=usuario_id,
                cliente_id=ctx.cliente_id,
                empresa_id=resolved_empresa_id,
            )
        return await execute_identity_query(
            query,
            cliente_id=ctx.cliente_id,
            identity_scope=scope,
        )

    @staticmethod
    async def detect_platform_superadmin(
        usuario_id: UUID,
        username: Optional[str] = None,
    ) -> bool:
        from app.core.config import settings

        if username and username == settings.SUPERADMIN_USERNAME:
            return True

        system_cliente_id = settings.SUPERADMIN_CLIENTE_ID
        if not system_cliente_id:
            return False
        try:
            system_uuid = UUID(str(system_cliente_id))
        except (ValueError, TypeError):
            return False

        query = text_platform_superadmin_count(
            usuario_id=usuario_id,
            system_cliente_id=system_uuid,
        )
        try:
            rows = await execute_platform_identity_query(
                query,
                platform_cliente_id=system_uuid,
            )
            if rows:
                return int(rows[0].get("super_admin_count") or 0) > 0
        except Exception as exc:
            logger.warning(
                "[IDENTITY] No se pudo verificar SUPER_ADMIN en cliente SYSTEM para %s: %s",
                usuario_id,
                exc,
            )
        return False

    @staticmethod
    async def lookup_user_for_auth_context(
        username: str,
        request_cliente_id: Optional[UUID],
    ) -> Optional[Dict[str, Any]]:
        """Lookup de usuario para deps auth (/me, RBAC) vía Identity Gateway."""
        from app.core.auth.platform_user_lookup import is_system_request_client
        from app.core.tenant.context import try_get_current_client_id

        if is_system_request_client(request_cliente_id) and request_cliente_id:
            return await IdentityGateway.get_platform_user_by_username(
                username,
                platform_cliente_id=request_cliente_id,
            )

        resolved_cliente_id = request_cliente_id or try_get_current_client_id()
        if not resolved_cliente_id:
            return None

        ctx = IdentityContext(cliente_id=resolved_cliente_id)
        user = await IdentityGateway.get_user_by_username(ctx, username)
        if user:
            return IdentityGateway.normalize_user_cliente_id(user, ctx)
        return None


__all__ = ["IdentityGateway"]
