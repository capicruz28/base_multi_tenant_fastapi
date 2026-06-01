# app/core/authorization/menu_resolver.py
"""
Menu Resolver centralizado (arquitectura SaaS enterprise).

Devuelve el menú del usuario ya filtrado por:
  - Módulos contratados del tenant (cliente_modulo)
  - Permisos efectivos del usuario (Permission Resolver como fuente de verdad)
  - Configuración del menú (modulo_menu + rol_menu_permiso)

Flujo documentado:
  Tenant → Modules (cliente_modulo) → Permissions (Permission Resolver) → Menu (ModuloMenuService).

No reemplaza GET /modulos-menus/me/; el nuevo endpoint GET /auth/menu consume este resolver.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.authorization.permission_resolver import get_permission_resolver
from app.core.authorization.menu_permission_resolver import resolve_required_permissions_for_menu_tree

logger = logging.getLogger(__name__)


class MenuResolverService:
    """
    Resuelve el menú del usuario usando Permission Resolver como fuente de permisos
    y ModuloMenuService para la estructura (módulos contratados + rol_menu_permiso).
    """

    async def get_menu_for_user(
        self,
        usuario_id: UUID,
        cliente_id: UUID,
        *,
        database_type: str = "single",
        is_super_admin: bool = False,
        as_tenant_admin: bool = False,
        empresa_id: UUID | None = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        """
        Devuelve el menú completo del usuario filtrado por tenant, módulos y permisos.

        Flujo:
          1. Tenant: cliente_id identifica el tenant.
          2. Modules: ModuloMenuService ya filtra por cliente_modulo (módulos activos).
          3. Permissions: se obtienen del Permission Resolver (cache reutilizado).
          4. Menu: ModuloMenuService.obtener_menu_usuario con effective_permission_codes.

        Returns:
            MenuUsuarioResponse (misma estructura que GET /modulos-menus/me/).
        """
        from app.modules.modulos.application.services.modulo_menu_service import (
            ModuloMenuService,
        )
        from app.core.auth.impersonation_rbac import (
            filter_menu_by_impersonation_permissions,
            is_impersonation_effective_tenant_session,
        )

        is_impersonation_menu = is_impersonation_effective_tenant_session(payload)
        if is_impersonation_menu and payload is None:
            is_impersonation_menu = False

        # 1. Permisos efectivos (impersonation_effective_admin reutiliza impersonation_rbac).
        resolver = get_permission_resolver()
        effective = await resolver.get_effective_permissions(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            database_type=database_type,
            is_super_admin=is_super_admin,
            filter_by_subscription=False,
            empresa_id=empresa_id,
            payload=payload if is_impersonation_menu else None,
        )
        permission_codes = list(effective.codes) if effective else []
        perm_source = getattr(effective, "source", "unknown")

        # 2. Menú: rol_menu_permiso (Modelo Owner). Impersonación → ADMIN_TENANT RMP directo.
        if is_impersonation_menu:
            menu = await ModuloMenuService.obtener_menu_impersonacion_tenant(
                usuario_id=usuario_id,
                cliente_id=cliente_id,
                empresa_id=empresa_id,
                effective_permission_codes=permission_codes,
            )
        else:
            menu = await ModuloMenuService.obtener_menu_usuario(
                usuario_id=usuario_id,
                cliente_id=cliente_id,
                is_super_admin=is_super_admin,
                as_tenant_admin=False,
                empresa_id=empresa_id,
                effective_permission_codes=permission_codes,
            )

        if is_impersonation_menu:
            modulos_antes = len(menu.modulos or [])
            menu = filter_menu_by_impersonation_permissions(menu, permission_codes)
            logger.info(
                "[IMPERSONATION-MENU] cliente_id=%s is_impersonation=true "
                "source_permissions=%s filtro_cliente_modulo=query_join "
                "filtro_permisos_impersonados=true modulos_antes=%s modulos_final=%s "
                "codigos_final=%s",
                cliente_id,
                perm_source,
                modulos_antes,
                len(menu.modulos or []),
                [getattr(m, "codigo", None) for m in (menu.modulos or [])],
            )

        try:
            await resolve_required_permissions_for_menu_tree(menu.modulos)
        except Exception as e:
            logger.warning(
                "%s Error no bloqueante resolviendo required_permission de menú: %s",
                "[RBAC]",
                e,
            )
        return menu


_menu_resolver_instance: MenuResolverService | None = None


def get_menu_resolver() -> MenuResolverService:
    global _menu_resolver_instance
    if _menu_resolver_instance is None:
        _menu_resolver_instance = MenuResolverService()
    return _menu_resolver_instance
