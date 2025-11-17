# app/core/connection_cache.py
"""
Sistema de cache para metadata de conexiones de clientes.

PROPÓSITO:
- Evitar consultas repetidas a cliente_modulo_conexion por cada request
- Reducir latencia en resolución de conexiones
- Permitir invalidación manual cuando cambia configuración

ESTRATEGIA:
- TTL de 5 minutos por defecto (configurable)
- Thread-safe con threading.Lock
- Invalidación manual por cliente_id
- Limpieza automática de entradas expiradas

USO:
    from app.core.connection_cache import connection_cache
    
    # Intentar obtener del cache
    metadata = connection_cache.get(client_id)
    
    if not metadata:
        # No está en cache, consultar BD
        metadata = query_database(client_id)
        # Guardar en cache
        connection_cache.set(client_id, metadata)
"""

import logging
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ConnectionMetadataCache:
    """
    Cache thread-safe para metadata de conexiones de clientes.
    
    Implementa un cache simple con TTL (Time To Live) para evitar
    consultas repetidas a la base de datos por cada request.
    """
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Inicializa el cache.
        
        Args:
            ttl_seconds: Tiempo de vida en segundos (default: 300 = 5 minutos)
        """
        self._cache: Dict[int, Dict[str, Any]] = {}
        self._timestamps: Dict[int, datetime] = {}
        self._lock = threading.Lock()
        self.ttl = timedelta(seconds=ttl_seconds)
        
        logger.info(f"✅ ConnectionMetadataCache inicializado (TTL: {ttl_seconds}s)")
    
    def get(self, client_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene metadata del cache si existe y no ha expirado.
        
        Args:
            client_id: ID del cliente
        
        Returns:
            Dict con metadata o None si no existe/expiró
        
        Ejemplo:
            >>> metadata = connection_cache.get(2)
            >>> if metadata:
            ...     print(f"DB: {metadata['nombre_bd']}")
        """
        with self._lock:
            if client_id not in self._cache:
                logger.debug(f"[CACHE MISS] Cliente {client_id} no está en cache")
                return None
            
            # Verificar expiración
            if datetime.now() - self._timestamps[client_id] >= self.ttl:
                logger.debug(f"[CACHE EXPIRED] Cliente {client_id} expiró, removiendo")
                del self._cache[client_id]
                del self._timestamps[client_id]
                return None
            
            logger.debug(f"[CACHE HIT] Cliente {client_id} encontrado en cache")
            return self._cache[client_id].copy()  # Retornar copia para evitar mutaciones
    
    def set(self, client_id: int, metadata: Dict[str, Any]) -> None:
        """
        Guarda metadata en el cache.
        
        Args:
            client_id: ID del cliente
            metadata: Dict con metadata de conexión
        
        Ejemplo:
            >>> metadata = {"database_type": "multi", "nombre_bd": "bd_cliente_acme"}
            >>> connection_cache.set(2, metadata)
        """
        with self._lock:
            self._cache[client_id] = metadata.copy()
            self._timestamps[client_id] = datetime.now()
            logger.debug(f"[CACHE SET] Cliente {client_id} guardado en cache")
    
    def invalidate(self, client_id: int) -> bool:
        """
        Invalida (elimina) la entrada de cache para un cliente específico.
        
        Útil cuando se actualiza la configuración de conexión de un cliente
        y se necesita forzar una nueva consulta a la BD.
        
        Args:
            client_id: ID del cliente a invalidar
        
        Returns:
            True si había entrada y fue eliminada, False si no existía
        
        Ejemplo:
            >>> connection_cache.invalidate(2)
            True
        """
        with self._lock:
            existed = client_id in self._cache
            
            if existed:
                del self._cache[client_id]
                del self._timestamps[client_id]
                logger.info(f"[CACHE INVALIDATE] Cliente {client_id} removido del cache")
            else:
                logger.debug(f"[CACHE INVALIDATE] Cliente {client_id} no estaba en cache")
            
            return existed
    
    def clear(self) -> int:
        """
        Limpia todo el cache.
        
        Returns:
            Cantidad de entradas eliminadas
        
        Ejemplo:
            >>> removed = connection_cache.clear()
            >>> print(f"Eliminadas {removed} entradas")
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._timestamps.clear()
            logger.info(f"[CACHE CLEAR] Cache limpiado ({count} entradas eliminadas)")
            return count
    
    def cleanup_expired(self) -> int:
        """
        Elimina entradas expiradas del cache.
        
        Esta función puede ser llamada periódicamente por un worker
        para evitar que el cache crezca indefinidamente.
        
        Returns:
            Cantidad de entradas eliminadas
        
        Ejemplo:
            >>> removed = connection_cache.cleanup_expired()
            >>> print(f"Limpiadas {removed} entradas expiradas")
        """
        with self._lock:
            now = datetime.now()
            expired_keys = [
                client_id 
                for client_id, timestamp in self._timestamps.items()
                if now - timestamp >= self.ttl
            ]
            
            for client_id in expired_keys:
                del self._cache[client_id]
                del self._timestamps[client_id]
            
            if expired_keys:
                logger.debug(f"[CACHE CLEANUP] Eliminadas {len(expired_keys)} entradas expiradas")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del cache.
        
        Returns:
            Dict con estadísticas (size, ttl, oldest_entry_age)
        
        Ejemplo:
            >>> stats = connection_cache.get_stats()
            >>> print(f"Cache size: {stats['size']}")
        """
        with self._lock:
            if not self._timestamps:
                oldest_age = None
            else:
                oldest_timestamp = min(self._timestamps.values())
                oldest_age = (datetime.now() - oldest_timestamp).total_seconds()
            
            return {
                "size": len(self._cache),
                "ttl_seconds": self.ttl.total_seconds(),
                "oldest_entry_age_seconds": oldest_age,
                "client_ids": list(self._cache.keys())
            }
    
    def __len__(self) -> int:
        """Retorna el tamaño actual del cache."""
        with self._lock:
            return len(self._cache)
    
    def __contains__(self, client_id: int) -> bool:
        """Verifica si un cliente está en el cache (sin verificar expiración)."""
        with self._lock:
            return client_id in self._cache
    
    def __repr__(self) -> str:
        """Representación string del cache."""
        return (
            f"ConnectionMetadataCache("
            f"size={len(self)}, "
            f"ttl={self.ttl.total_seconds()}s"
            f")"
        )


# ============================================
# INSTANCIA GLOBAL DEL CACHE
# ============================================

# Instancia singleton del cache (5 minutos TTL por defecto)
connection_cache = ConnectionMetadataCache(ttl_seconds=300)

# Para testing o configuración custom, puedes crear instancias adicionales:
# custom_cache = ConnectionMetadataCache(ttl_seconds=600)  # 10 minutos


# ============================================
# FUNCIONES HELPER PARA MONITOREO
# ============================================

def get_cache_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas del cache global.
    
    Útil para endpoints de monitoreo/health check.
    
    Returns:
        Dict con estadísticas del cache
    
    Ejemplo:
        >>> stats = get_cache_stats()
        >>> print(stats)
        {'size': 5, 'ttl_seconds': 300, ...}
    """
    return connection_cache.get_stats()


def invalidate_client_cache(client_id: int) -> bool:
    """
    Invalida el cache para un cliente específico.
    
    Wrapper convenience para invalidación desde otros módulos.
    
    Args:
        client_id: ID del cliente
    
    Returns:
        True si se invalidó, False si no existía
    
    Ejemplo:
        >>> invalidate_client_cache(2)
        True
    """
    return connection_cache.invalidate(client_id)


def clear_all_cache() -> int:
    """
    Limpia todo el cache.
    
    Wrapper convenience para limpieza total.
    
    Returns:
        Cantidad de entradas eliminadas
    
    Ejemplo:
        >>> cleared = clear_all_cache()
        >>> print(f"Cache limpiado: {cleared} entradas")
    """
    return connection_cache.clear()


# ============================================
# LOGGING DE INICIALIZACIÓN
# ============================================

logger.info(
    f"Módulo connection_cache cargado. "
    f"Cache global: {connection_cache}"
)