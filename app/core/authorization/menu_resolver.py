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

        # 1. Permisos efectivos desde Permission Resolver (única fuente de verdad; reutiliza cache).
        resolver = get_permission_resolver()
        effective = await resolver.get_effective_permissions(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            database_type=database_type,
            is_super_admin=is_super_admin,
            filter_by_subscription=False,
        )
        permission_codes = list(effective.codes) if effective else []

        # 2. Menú desde ModuloMenuService (ya filtra por módulos contratados y rol_menu_permiso).
        # Se pasan los permisos efectivos por si en el futuro se filtra por permiso por ítem.
        menu = await ModuloMenuService.obtener_menu_usuario(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            is_super_admin=is_super_admin,
            as_tenant_admin=as_tenant_admin,
            effective_permission_codes=permission_codes,
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
