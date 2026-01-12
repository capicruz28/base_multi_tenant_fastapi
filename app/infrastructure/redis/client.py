# app/infrastructure/redis/client.py
"""
Servicio Redis asíncrono para gestión de blacklist de tokens.

✅ REVOCACIÓN DE TOKENS: Implementa blacklist usando Redis con TTL automático.
- Usa redis.asyncio para operaciones asíncronas
- Fail-soft: Si Redis no está disponible, el sistema continúa funcionando
- TTL automático basado en tiempo de expiración del token
"""

import logging
from typing import Optional
from uuid import UUID
import redis.asyncio as aioredis
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================
# CLIENTE REDIS ASÍNCRONO (SINGLETON)
# ============================================

_redis_client: Optional[aioredis.Redis] = None
_redis_enabled: bool = False


async def _get_redis_client() -> Optional[aioredis.Redis]:
    """
    Obtiene o crea el cliente Redis asíncrono.
    
    Returns:
        Cliente Redis asíncrono o None si no está disponible
    """
    global _redis_client, _redis_enabled
    
    # Si ya está inicializado, retornarlo
    if _redis_client is not None:
        return _redis_client
    
    # Si Redis está deshabilitado, retornar None
    if not settings.ENABLE_REDIS_CACHE:
        logger.debug("[REDIS_BLACKLIST] Redis desactivado en configuración")
        return None
    
    try:
        _redis_client = aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_SOCKET_TIMEOUT,
            decode_responses=True,
            retry_on_timeout=True,
        )
        
        # Test de conexión
        await _redis_client.ping()
        
        _redis_enabled = True
        logger.info(
            f"[REDIS_BLACKLIST] Cliente Redis asíncrono conectado. "
            f"Host={settings.REDIS_HOST}:{settings.REDIS_PORT}, DB={settings.REDIS_DB}"
        )
        
        return _redis_client
        
    except ImportError:
        logger.warning(
            "[REDIS_BLACKLIST] redis no instalado. "
            "Instalar con: pip install redis. "
            "Blacklist de tokens desactivada (fail-soft)."
        )
        _redis_enabled = False
        return None
    except Exception as e:
        logger.error(
            f"[REDIS_BLACKLIST] ❌ Error conectando a Redis: {str(e)}. "
            f"Host={settings.REDIS_HOST}:{settings.REDIS_PORT}, DB={settings.REDIS_DB}. "
            "Blacklist de tokens desactivada (fail-soft). "
            "El sistema continuará funcionando pero sin revocación de tokens.",
            exc_info=True
        )
        _redis_enabled = False
        return None


async def _close_redis_client():
    """Cierra la conexión Redis si está abierta."""
    global _redis_client, _redis_enabled
    
    if _redis_client:
        try:
            await _redis_client.close()
            logger.info("[REDIS_BLACKLIST] Cliente Redis cerrado")
        except Exception as e:
            logger.warning(f"[REDIS_BLACKLIST] Error cerrando cliente Redis: {e}")
        finally:
            _redis_client = None
            _redis_enabled = False


# ============================================
# SERVICIO REDIS PARA BLACKLIST
# ============================================

class RedisService:
    """
    Servicio para gestión de blacklist de tokens en Redis.
    
    ✅ REVOCACIÓN DE TOKENS:
    - set_token_blacklist: Agrega un token a la blacklist con TTL
    - is_token_blacklisted: Verifica si un token está en la blacklist
    
    ✅ FAIL-SOFT:
    - Si Redis no está disponible, las operaciones fallan silenciosamente
    - El sistema continúa funcionando sin blacklist
    """
    
    # Prefijo para claves de blacklist
    BLACKLIST_PREFIX = "blacklist:token:"
    
    @staticmethod
    async def set_token_blacklist(jti: str, expire_seconds: int) -> bool:
        """
        Agrega un token a la blacklist con TTL automático.
        
        Args:
            jti: JWT ID (identificador único del token)
            expire_seconds: Tiempo de vida en segundos (TTL en Redis)
        
        Returns:
            True si se agregó exitosamente, False si falló (fail-soft)
        """
        if expire_seconds <= 0:
            logger.warning(f"[REDIS_BLACKLIST] TTL inválido para jti {jti}: {expire_seconds}")
            return False
        
        client = await _get_redis_client()
        if not client:
            logger.warning(
                f"[REDIS_BLACKLIST] ⚠️ Redis no disponible, no se puede agregar jti {jti} a blacklist (fail-soft). "
                f"Verificar: REDIS_HOST={settings.REDIS_HOST}, REDIS_PORT={settings.REDIS_PORT}, "
                f"ENABLE_REDIS_CACHE={settings.ENABLE_REDIS_CACHE}"
            )
            return False
        
        try:
            key = f"{RedisService.BLACKLIST_PREFIX}{jti}"
            # Guardar con TTL (expira automáticamente)
            await client.setex(key, expire_seconds, "revoked")
            
            logger.info(
                f"[REDIS_BLACKLIST] Token revocado: jti={jti}, "
                f"TTL={expire_seconds}s (expira en {expire_seconds // 60} min)"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"[REDIS_BLACKLIST] Error agregando token a blacklist (jti={jti}): {e}. "
                "Continuando sin blacklist (fail-soft)",
                exc_info=True
            )
            return False
    
    @staticmethod
    async def is_token_blacklisted(jti: str) -> bool:
        """
        Verifica si un token está en la blacklist.
        
        Args:
            jti: JWT ID (identificador único del token)
        
        Returns:
            True si el token está en la blacklist, False si no está o Redis no está disponible
        """
        client = await _get_redis_client()
        if not client:
            # Fail-soft: Si Redis no está disponible, asumir que el token NO está revocado
            logger.warning(
                f"[REDIS_BLACKLIST] ⚠️ Redis no disponible, asumiendo token válido (fail-soft). "
                f"Verificar: REDIS_HOST={settings.REDIS_HOST}, REDIS_PORT={settings.REDIS_PORT}, "
                f"ENABLE_REDIS_CACHE={settings.ENABLE_REDIS_CACHE}. "
                f"jti={jti}"
            )
            return False
        
        try:
            key = f"{RedisService.BLACKLIST_PREFIX}{jti}"
            exists = await client.exists(key)
            
            if exists:
                logger.debug(f"[REDIS_BLACKLIST] Token revocado detectado: jti={jti}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(
                f"[REDIS_BLACKLIST] Error verificando blacklist (jti={jti}): {e}. "
                "Asumiendo token válido (fail-soft)",
                exc_info=True
            )
            # Fail-soft: En caso de error, asumir que el token NO está revocado
            return False
    
    @staticmethod
    async def get_token_ttl(jti: str) -> Optional[int]:
        """
        Obtiene el TTL restante de un token en la blacklist.
        
        Args:
            jti: JWT ID (identificador único del token)
        
        Returns:
            TTL en segundos o None si no existe o Redis no está disponible
        """
        client = await _get_redis_client()
        if not client:
            return None
        
        try:
            key = f"{RedisService.BLACKLIST_PREFIX}{jti}"
            ttl = await client.ttl(key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.warning(f"[REDIS_BLACKLIST] Error obteniendo TTL para jti {jti}: {e}")
            return None
    
    @staticmethod
    def is_redis_available() -> bool:
        """
        Verifica si Redis está disponible.
        
        Returns:
            True si Redis está disponible, False en caso contrario
        """
        return _redis_enabled


# ============================================
# LOGGING DE INICIALIZACIÓN
# ============================================

# Nota: La inicialización real ocurre en la primera llamada a _get_redis_client()
logger.info("Módulo RedisService cargado (blacklist de tokens con fail-soft)")

