# app/core/security/rate_limiting.py
"""
Sistema de Rate Limiting para protección contra ataques de fuerza bruta.

✅ FASE 1: ACTIVADO POR DEFECTO
- Por defecto está ACTIVADO (ENABLE_RATE_LIMITING=True)
- Para desactivar, establecer ENABLE_RATE_LIMITING=false en .env
- Límites generosos para no afectar uso normal (10 login/min, 200 API/min)
- Fallback automático si falla (se desactiva si slowapi no está instalado)

USO:
    from app.core.security.rate_limiting import limiter, get_rate_limit_decorator
    
    @router.post("/login/")
    @get_rate_limit_decorator("login")
    async def login(...):
        ...
"""

import logging
from typing import Optional, Callable
from functools import wraps

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================
# INICIALIZACIÓN DE SLOWAPI (CONDICIONAL)
# ============================================

_limiter = None
_limiter_enabled = False

def _initialize_limiter():
    """Inicializa slowapi solo si el rate limiting está habilitado."""
    global _limiter, _limiter_enabled
    
    if not settings.ENABLE_RATE_LIMITING:
        logger.info("[RATE_LIMITING] Desactivado (configurado manualmente)")
        _limiter_enabled = False
        return None
    
    try:
        from slowapi import Limiter
        from slowapi.util import get_remote_address
        from slowapi.errors import RateLimitExceeded
        
        _limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[],  # Sin límites por defecto (se definen por endpoint)
            storage_uri="memory://",  # Almacenamiento en memoria (simple)
            headers_enabled=True  # Incluir headers de rate limit en respuesta
        )
        
        _limiter_enabled = True
        logger.info(
            f"[RATE_LIMITING] Activado. "
            f"Límites: Login={settings.RATE_LIMIT_LOGIN}, API={settings.RATE_LIMIT_API}"
        )
        
        return _limiter
        
    except ImportError:
        logger.warning(
            "[RATE_LIMITING] slowapi no instalado. "
            "Instalar con: pip install slowapi"
        )
        _limiter_enabled = False
        return None
    except Exception as e:
        logger.error(
            f"[RATE_LIMITING] Error al inicializar: {str(e)}. "
            "Rate limiting desactivado (fallback seguro)"
        )
        _limiter_enabled = False
        return None

# Inicializar al importar el módulo
_limiter = _initialize_limiter()

# ============================================
# FUNCIONES PÚBLICAS
# ============================================

def get_limiter():
    """
    Obtiene la instancia de Limiter (solo si está habilitado).
    
    Returns:
        Limiter instance o None si está desactivado
    """
    if not _limiter_enabled:
        return None
    return _limiter


def get_rate_limit_decorator(limit_type: str = "api") -> Callable:
    """
    Obtiene un decorador de rate limiting según el tipo.
    
    ✅ FASE 1: Decorador condicional para FastAPI
    - Si rate limiting está desactivado, retorna decorador que no hace nada
    - Si está activado, retorna decorador de slowapi compatible con FastAPI
    
    Args:
        limit_type: Tipo de límite ("login" o "api")
    
    Returns:
        Decorador de rate limiting o decorador vacío
    """
    if not _limiter_enabled or _limiter is None:
        # ✅ FALLBACK: Decorador que no hace nada (comportamiento actual)
        def noop_decorator(func):
            return func
        return noop_decorator
    
    # Obtener límite según tipo
    if limit_type == "login":
        limit = settings.RATE_LIMIT_LOGIN
    elif limit_type == "api":
        limit = settings.RATE_LIMIT_API
    else:
        limit = settings.RATE_LIMIT_API  # Default
    
    # Retornar decorador de slowapi (compatible con FastAPI)
    # El decorador se aplica después de @router.post()
    return _limiter.limit(limit)


def is_rate_limiting_enabled() -> bool:
    """
    Verifica si el rate limiting está habilitado.
    
    Returns:
        True si está habilitado, False si no
    """
    return _limiter_enabled


# ============================================
# EXCEPCIÓN PERSONALIZADA (OPCIONAL)
# ============================================

class RateLimitExceededError(Exception):
    """Excepción personalizada para rate limit excedido."""
    def __init__(self, detail: str = "Demasiadas solicitudes. Por favor, intente más tarde."):
        self.detail = detail
        super().__init__(self.detail)


# ============================================
# LOGGING DE INICIALIZACIÓN
# ============================================

if _limiter_enabled:
    logger.info("✅ Módulo de rate limiting cargado y activo")
else:
    logger.info("ℹ️ Módulo de rate limiting cargado pero desactivado (configurado manualmente)")

