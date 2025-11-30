# app/infrastructure/cache/redis_cache.py
"""
Sistema de Cache Distribuido con Redis.

✅ FASE 2: PERFORMANCE - ACTIVADO POR DEFECTO
- Por defecto está ACTIVADO (ENABLE_REDIS_CACHE=True)
- Para desactivar, establecer ENABLE_REDIS_CACHE=false en .env
- Fallback automático a cache en memoria si Redis no está disponible
- Útil para múltiples instancias del servidor

CARACTERÍSTICAS:
- Cache distribuido (compartido entre instancias)
- TTL configurable por clave
- Fallback seguro si Redis falla
- Compatible con sistema multi-tenant
"""

import logging
from typing import Optional, Any
import json
from functools import wraps

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================
# CLIENTE REDIS (SINGLETON)
# ============================================

_redis_client = None
_redis_enabled = False
_cache_fallback = {}  # Cache en memoria como fallback

def _initialize_redis():
    """Inicializa cliente Redis si está habilitado."""
    global _redis_client, _redis_enabled
    
    if not settings.ENABLE_REDIS_CACHE:
        logger.info("[REDIS_CACHE] Desactivado (configurado manualmente)")
        _redis_enabled = False
        return None
    
    try:
        import redis
        
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_SOCKET_TIMEOUT,
            decode_responses=True,  # Retornar strings en lugar de bytes
            retry_on_timeout=True
        )
        
        # Test de conexión
        _redis_client.ping()
        
        _redis_enabled = True
        logger.info(
            f"[REDIS_CACHE] Conectado exitosamente. "
            f"Host={settings.REDIS_HOST}:{settings.REDIS_PORT}, DB={settings.REDIS_DB}"
        )
        
        return _redis_client
        
    except ImportError:
        logger.warning(
            "[REDIS_CACHE] redis no instalado. "
            "Instalar con: pip install redis. "
            "Cache desactivado automáticamente (usando fallback en memoria)."
        )
        _redis_enabled = False
        return None
    except Exception as e:
        logger.warning(
            f"[REDIS_CACHE] Error conectando a Redis: {str(e)}. "
            "Cache desactivado automáticamente (usando fallback en memoria)."
        )
        _redis_enabled = False
        return None

# Inicializar al importar
_redis_client = _initialize_redis()


# ============================================
# FUNCIONES PÚBLICAS
# ============================================

def get_cached(key: str, default: Any = None) -> Optional[Any]:
    """
    Obtiene valor del cache (Redis o memoria).
    
    ✅ FASE 2: Cache con fallback
    - Intenta obtener de Redis primero
    - Si falla, usa cache en memoria
    - Si no existe, retorna default
    
    Args:
        key: Clave del cache
        default: Valor por defecto si no existe
    
    Returns:
        Valor cacheado o default
    """
    if not _redis_enabled:
        # Fallback: cache en memoria
        return _cache_fallback.get(key, default)
    
    try:
        value = _redis_client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Si no es JSON, retornar como string
                return value
        return default
        
    except Exception as e:
        logger.warning(
            f"[REDIS_CACHE] Error leyendo cache para key '{key}': {e}. "
            "Usando fallback en memoria"
        )
        # Fallback: cache en memoria
        return _cache_fallback.get(key, default)


def set_cached(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """
    Guarda valor en cache (Redis o memoria).
    
    ✅ FASE 2: Cache con fallback
    - Intenta guardar en Redis primero
    - Si falla, guarda en memoria
    
    Args:
        key: Clave del cache
        value: Valor a cachear (debe ser serializable a JSON)
        ttl: Tiempo de vida en segundos (None = usar default)
    
    Returns:
        True si se guardó exitosamente, False si falló
    """
    if ttl is None:
        ttl = settings.CACHE_DEFAULT_TTL
    
    if not _redis_enabled:
        # Fallback: cache en memoria (sin TTL real, solo guardar)
        _cache_fallback[key] = value
        return True
    
    try:
        # Serializar a JSON
        if isinstance(value, str):
            serialized = value
        else:
            serialized = json.dumps(value)
        
        # Guardar en Redis con TTL
        _redis_client.setex(key, ttl, serialized)
        return True
        
    except Exception as e:
        logger.warning(
            f"[REDIS_CACHE] Error guardando cache para key '{key}': {e}. "
            "Usando fallback en memoria"
        )
        # Fallback: cache en memoria
        _cache_fallback[key] = value
        return True


def delete_cached(key: str) -> bool:
    """
    Elimina una clave del cache.
    
    Args:
        key: Clave a eliminar
    
    Returns:
        True si se eliminó, False si no existía o falló
    """
    if not _redis_enabled:
        # Fallback: cache en memoria
        _cache_fallback.pop(key, None)
        return True
    
    try:
        deleted = _redis_client.delete(key)
        return deleted > 0
    except Exception as e:
        logger.warning(f"[REDIS_CACHE] Error eliminando cache para key '{key}': {e}")
        # Fallback: cache en memoria
        _cache_fallback.pop(key, None)
        return True


def clear_cache_pattern(pattern: str) -> int:
    """
    Elimina todas las claves que coincidan con un patrón.
    
    Útil para invalidar cache de un tenant o módulo.
    
    Args:
        pattern: Patrón (ej: "tenant_2:*" o "connection_metadata:*")
    
    Returns:
        Número de claves eliminadas
    """
    if not _redis_enabled:
        # Fallback: cache en memoria
        count = 0
        keys_to_delete = [k for k in _cache_fallback.keys() if pattern.replace('*', '') in k]
        for key in keys_to_delete:
            _cache_fallback.pop(key, None)
            count += 1
        return count
    
    try:
        keys = _redis_client.keys(pattern)
        if keys:
            return _redis_client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"[REDIS_CACHE] Error limpiando cache con patrón '{pattern}': {e}")
        return 0


def is_cache_enabled() -> bool:
    """Verifica si el cache está habilitado."""
    return _redis_enabled or settings.ENABLE_REDIS_CACHE


def get_cache_info() -> dict:
    """
    Obtiene información del estado del cache.
    
    Returns:
        Dict con información del cache
    """
    return {
        "enabled": _redis_enabled,
        "type": "redis" if _redis_enabled else "memory",
        "host": settings.REDIS_HOST if _redis_enabled else None,
        "port": settings.REDIS_PORT if _redis_enabled else None,
        "fallback_size": len(_cache_fallback) if not _redis_enabled else 0
    }


# ============================================
# DECORADOR PARA CACHEAR FUNCIONES
# ============================================

def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorador para cachear resultados de funciones.
    
    ✅ FASE 2: Cache automático con fallback
    
    Uso:
        @cached(ttl=300, key_prefix="user_")
        async def get_user(user_id: int):
            ...
    
    Args:
        ttl: Tiempo de vida en segundos (None = usar default)
        key_prefix: Prefijo para las claves de cache
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Construir clave de cache
            cache_key = f"{key_prefix}{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Intentar obtener del cache
            cached_value = get_cached(cache_key)
            if cached_value is not None:
                logger.debug(f"[CACHE] HIT para {func.__name__}: {cache_key}")
                return cached_value
            
            # Ejecutar función
            result = await func(*args, **kwargs)
            
            # Guardar en cache
            set_cached(cache_key, result, ttl)
            logger.debug(f"[CACHE] MISS para {func.__name__}: {cache_key} (guardado)")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Construir clave de cache
            cache_key = f"{key_prefix}{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Intentar obtener del cache
            cached_value = get_cached(cache_key)
            if cached_value is not None:
                logger.debug(f"[CACHE] HIT para {func.__name__}: {cache_key}")
                return cached_value
            
            # Ejecutar función
            result = func(*args, **kwargs)
            
            # Guardar en cache
            set_cached(cache_key, result, ttl)
            logger.debug(f"[CACHE] MISS para {func.__name__}: {cache_key} (guardado)")
            
            return result
        
        # Retornar wrapper según si la función es async o sync
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ============================================
# LOGGING DE INICIALIZACIÓN
# ============================================

if _redis_enabled:
    logger.info("✅ Módulo de Redis cache cargado y activo")
else:
    logger.info("ℹ️ Módulo de Redis cache cargado pero desactivado (usando fallback en memoria)")

