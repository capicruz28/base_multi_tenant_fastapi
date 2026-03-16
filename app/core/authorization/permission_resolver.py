# app/core/authorization/permission_resolver.py
"""
Permission Resolver (Stage 1 - Fase A).

Servicio que resuelve permisos efectivos por (usuario_id, cliente_id) con cache opcional
y atajo para super_admin. Integrado en build_user_with_roles bajo feature flag con fallback.

Flujo de resolución (comentado en get_effective_permissions):
  Usuario → Roles (usuario_rol) → Permisos (rol_permiso ⋈ permiso)
  → Módulos contratados (cliente_modulo) → Permisos finales.
"""

from __future__ import annotations

import logging
from typing import List
from uuid import UUID

from app.core.config import settings
from app.core.authorization.effective_permissions import EffectivePermissions, SourceType
from app.core.authorization.permission_cache import get_permission_cache

logger = logging.getLogger(__name__)


async def _get_active_module_codes_for_tenant_async(cliente_id: UUID) -> List[str]:
    try:
        from sqlalchemy import text
        from app.infrastructure.database.queries_async import execute_query
        from app.infrastructure.database.connection_async import DatabaseConnection

        sql = text("""
            SELECT m.codigo
            FROM cliente_modulo cm
            INNER JOIN modulo m ON m.modulo_id = cm.modulo_id AND m.es_activo = 1
            WHERE cm.cliente_id = :cliente_id
              AND cm.esta_activo = 1
              AND (cm.fecha_vencimiento IS NULL OR cm.fecha_vencimiento > CAST(GETDATE() AS DATE))
        """).bindparams(cliente_id=cliente_id)
        rows = await execute_query(sql, connection_type=DatabaseConnection.ADMIN)
    except Exception as e:
        logger.warning("[PERMISSION_RESOLVER] No se pudieron cargar módulos activos para %s: %s", cliente_id, e)
        return []
    if not rows:
        return []
    return [str(r.get("codigo", "")).strip().lower() for r in rows if r.get("codigo")]


def _filter_codes_by_subscription(codes: List[str], active_module_codes: List[str]) -> List[str]:
    """Mantiene solo códigos cuyo prefijo está en active_module_codes o es admin/modulos."""
    PREFIJOS_GLOBALES = {"admin", "modulos"}
    allowed = set(active_module_codes) | PREFIJOS_GLOBALES
    result = []
    for code in codes:
        if not code or "." not in code:
            result.append(code)
            continue
        prefix = code.split(".", 1)[0].strip().lower()
        if prefix in allowed:
            result.append(code)
    return result


class PermissionResolverService:
    """
    Resuelve permisos efectivos para (usuario_id, cliente_id).
    No cachea super_admin; opcionalmente cachea resultados de BD.
    Siempre filtra por módulos contratados del tenant (cliente_modulo + permiso.modulo_id).
    """

    async def get_effective_permissions(
        self,
        usuario_id: UUID,
        cliente_id: UUID,
        *,
        database_type: str = "single",
        is_super_admin: bool = False,
        filter_by_subscription: bool = False,
    ) -> EffectivePermissions:
        """
        Calcula permisos efectivos. Si is_super_admin=True no consulta BD ni cache.

        Flujo:
          1. Usuario: identificado por (usuario_id, cliente_id).
          2. Roles: usuario_rol (roles asignados al usuario en el tenant).
          3. Permisos: rol_permiso ⋈ permiso (códigos de permiso de esos roles).
          4. Módulos contratados: cliente_modulo (módulos activos del tenant; billing).
          5. Permisos finales: solo códigos cuyo permiso.modulo_id es NULL (globales)
             o está en cliente_modulo activos. Fuente de verdad: permiso.modulo_id.
        """
        if is_super_admin:
            logger.debug("[PERMISSION_RESOLVER] super_admin bypass para usuario %s", usuario_id)
            return EffectivePermissions(
                codes=[],
                is_super_admin=True,
                cliente_id=cliente_id,
                usuario_id=usuario_id,
                source="super_admin",
            )

        cache_enabled = getattr(settings, "PERMISSION_RESOLVER_CACHE_ENABLED", False)
        if cache_enabled:
            cache = get_permission_cache(ttl_seconds=getattr(settings, "PERMISSION_RESOLVER_CACHE_TTL", 300))
            cached = cache.get(cliente_id, usuario_id)
            if cached is not None:
                logger.debug("[PERMISSION_RESOLVER] cache hit for %s in tenant %s", usuario_id, cliente_id)
                return cached

        # Usuario → Roles → Permisos → Módulos contratados (cliente_modulo) → Permisos finales.
        # obtener_codigos_permiso_usuario con filter_by_active_modules=True aplica el filtro
        # por permiso.modulo_id y cliente_modulo en la capa de datos.
        from app.modules.rbac.application.services.permisos_usuario_service import (
            obtener_codigos_permiso_usuario,
        )

        codes = await obtener_codigos_permiso_usuario(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            database_type=database_type,
            filter_by_active_modules=True,
        )

        # Opcional: filtro adicional por prefijo de código (compatibilidad con filter_by_subscription).
        active_module_codes: List[str] | None = None
        if filter_by_subscription:
            active_module_codes = await _get_active_module_codes_for_tenant_async(cliente_id)
            codes = _filter_codes_by_subscription(codes, active_module_codes)

        effective = EffectivePermissions(
            codes=codes,
            is_super_admin=False,
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            active_module_codes=active_module_codes,
            source="database",
        )

        if cache_enabled:
            cache = get_permission_cache(ttl_seconds=getattr(settings, "PERMISSION_RESOLVER_CACHE_TTL", 300))
            cache.set(cliente_id, usuario_id, effective)

        return effective

    def invalidate_for_user(self, usuario_id: UUID, cliente_id: UUID) -> None:
        """Invalida cache para ese usuario en ese tenant (tras cambios en usuario_rol)."""
        if not getattr(settings, "PERMISSION_RESOLVER_CACHE_ENABLED", False):
            return
        cache = get_permission_cache()
        cache.invalidate_for_user(usuario_id, cliente_id)

    def invalidate_for_tenant(self, cliente_id: UUID) -> None:
        """Invalida todas las entradas de cache del tenant (tras cambios en rol_permiso o cliente_modulo)."""
        if not getattr(settings, "PERMISSION_RESOLVER_CACHE_ENABLED", False):
            return
        cache = get_permission_cache()
        cache.invalidate_for_tenant(cliente_id)

    async def get_active_module_codes(self, cliente_id: UUID) -> List[str]:
        """
        Devuelve los códigos de módulos activos del tenant (cliente_modulo + modulo).
        Para billing/feature-flags: usar este método en lugar de consultar cliente_modulo directamente.
        """
        return await _get_active_module_codes_for_tenant_async(cliente_id)


# Singleton para uso desde build_user_with_roles e invalidaciones
_resolver_instance: PermissionResolverService | None = None


def get_permission_resolver() -> PermissionResolverService:
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = PermissionResolverService()
    return _resolver_instance
