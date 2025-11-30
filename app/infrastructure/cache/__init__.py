# app/infrastructure/cache/__init__.py
"""
Módulo de cache distribuido con Redis.

✅ FASE 2: PERFORMANCE
- Cache distribuido con Redis (opcional)
- Fallback a cache en memoria si Redis no está disponible
"""

from app.infrastructure.cache.redis_cache import (
    get_cached,
    set_cached,
    delete_cached,
    clear_cache_pattern,
    is_cache_enabled,
    get_cache_info,
    cached
)

__all__ = [
    "get_cached",
    "set_cached",
    "delete_cached",
    "clear_cache_pattern",
    "is_cache_enabled",
    "get_cache_info",
    "cached"
]

