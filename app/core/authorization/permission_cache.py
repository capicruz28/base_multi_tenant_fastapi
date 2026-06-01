# app/core/authorization/permission_cache.py
"""
Capa de cache desacoplada para permisos efectivos (Stage 1).

- In-memory con TTL por entrada.
- Clave: permissions:{cliente_id}:{usuario_id} (UUIDs en str canónico).
- No se usa Redis aquí para mantener Stage 1 simple; se puede sustituir por Redis después.
"""

from __future__ import annotations

import logging
import time
from typing import Optional
from uuid import UUID

from app.core.authorization.effective_permissions import EffectivePermissions

logger = logging.getLogger(__name__)


def _cache_key(
    cliente_id: UUID,
    usuario_id: UUID,
    empresa_id: Optional[UUID] = None,
) -> str:
    emp = str(empresa_id) if empresa_id else "none"
    return f"permissions:{cliente_id!s}:{usuario_id!s}:{emp}"


class PermissionCache:
    """
    Cache en memoria para EffectivePermissions con TTL.
    Thread-safe básico (dict + timestamp); para producción con múltiples workers
    se puede reemplazar por Redis usando el mismo contrato.
    """

    def __init__(self, ttl_seconds: int = 300):
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[EffectivePermissions, float]] = {}

    def get(
        self,
        cliente_id: UUID,
        usuario_id: UUID,
        empresa_id: Optional[UUID] = None,
    ) -> Optional[EffectivePermissions]:
        key = _cache_key(cliente_id, usuario_id, empresa_id)
        entry = self._store.get(key)
        if not entry:
            return None
        effective, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return effective

    def set(
        self,
        cliente_id: UUID,
        usuario_id: UUID,
        effective: EffectivePermissions,
        ttl_seconds: Optional[int] = None,
        empresa_id: Optional[UUID] = None,
    ) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._ttl
        key = _cache_key(cliente_id, usuario_id, empresa_id)
        self._store[key] = (effective, time.monotonic() + ttl)

    def invalidate_for_user(self, usuario_id: UUID, cliente_id: UUID) -> None:
        prefix = f"permissions:{cliente_id!s}:{usuario_id!s}:"
        to_remove = [k for k in self._store if k.startswith(prefix)]
        for k in to_remove:
            del self._store[k]
        if to_remove:
            logger.debug(
                "Permission cache invalidated for user %s in tenant %s (%d keys)",
                usuario_id,
                cliente_id,
                len(to_remove),
            )

    def invalidate_for_tenant(self, cliente_id: UUID) -> None:
        prefix = f"permissions:{cliente_id!s}:"
        to_remove = [k for k in self._store if k.startswith(prefix)]
        for k in to_remove:
            del self._store[k]
        if to_remove:
            logger.debug("Permission cache invalidated for tenant %s (%d keys)", cliente_id, len(to_remove))


# Singleton usado por el resolver cuando el cache está habilitado
_permission_cache: Optional[PermissionCache] = None


def get_permission_cache(ttl_seconds: int = 300) -> PermissionCache:
    global _permission_cache
    if _permission_cache is None:
        _permission_cache = PermissionCache(ttl_seconds=ttl_seconds)
    return _permission_cache
