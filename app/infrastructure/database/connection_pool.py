# app/infrastructure/database/connection_pool.py
"""
Sistema de Connection Pooling para mejorar performance.

✅ FASE 2: PERFORMANCE - ACTIVADO POR DEFECTO
- Por defecto está ACTIVADO (ENABLE_CONNECTION_POOLING=True)
- Para desactivar, establecer ENABLE_CONNECTION_POOLING=false en .env
- Usa SQLAlchemy para pooling (compatible con pyodbc)
- Fallback automático a conexiones directas si falla

✅ CORRECCIÓN CRÍTICA: Pooling dinámico con límites y limpieza automática
- Límite máximo de pools activos (evita colapso con muchos tenants)
- Limpieza automática de pools inactivos (LRU)
- Pool size reducido para tenants (optimizado para multi-tenant)

CARACTERÍSTICAS:
- Pool de conexiones reutilizables
- Mejor performance en alta concurrencia
- Compatible con sistema multi-tenant híbrido
- Fallback seguro si pool falla
- Gestión inteligente de pools (límites y limpieza)
"""

import logging
import os
from typing import Optional, Dict, Any, Tuple
from contextlib import contextmanager
from datetime import datetime, timedelta
import pyodbc
from collections import OrderedDict

from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.infrastructure.database.connection_async import DatabaseConnection

logger = logging.getLogger(__name__)

# ============================================
# POOLS POR TIPO DE CONEXIÓN
# ============================================

_pools: Dict[str, Any] = {}
_pool_access_times: OrderedDict[str, datetime] = OrderedDict()  # LRU tracking
_pool_enabled = False

# ✅ FASE 0: Aumentar límites para soportar 100+ tenants dedicados
# ✅ CORRECCIÓN: Configuración de límites optimizada para escalabilidad
MAX_TENANT_POOLS = int(os.getenv("MAX_TENANT_POOLS", "200"))  # Máximo 200 pools de tenants (aumentado de 50)
POOL_INACTIVITY_TIMEOUT = int(os.getenv("POOL_INACTIVITY_TIMEOUT", "1800"))  # 30 minutos sin uso (reducido de 1 hora)
TENANT_POOL_SIZE = int(os.getenv("TENANT_POOL_SIZE", "5"))  # Pool size aumentado para tenants (de 3 a 5)
TENANT_POOL_MAX_OVERFLOW = int(os.getenv("TENANT_POOL_MAX_OVERFLOW", "3"))  # Overflow aumentado (de 2 a 3)

def _initialize_pools():
    """Inicializa pools de conexión si está habilitado."""
    global _pools, _pool_enabled
    
    if not settings.ENABLE_CONNECTION_POOLING:
        logger.info("[CONNECTION_POOL] Desactivado (configurado manualmente)")
        _pool_enabled = False
        return
    
    try:
        # ✅ CORRECCIÓN: Import defensivo para Python 3.13
        # El error de SQLAlchemy 2.0.44 con Python 3.13 ocurre durante la importación
        # Capturamos el error específico y desactivamos pooling de forma segura
        try:
            import sys
            # Suprimir el error de AssertionError durante la importación
            # Esto es un workaround para el bug conocido de SQLAlchemy 2.0.44 + Python 3.13
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from sqlalchemy import create_engine, pool
                from sqlalchemy.pool import QueuePool
                from urllib.parse import quote_plus
        except (AssertionError, ImportError, AttributeError, Exception) as import_err:
            # Error conocido: SQLAlchemy 2.0.44 + Python 3.13
            error_str = str(import_err)
            if "TypingOnly" in error_str or "SQLCoreOperations" in error_str:
                logger.warning(
                    f"[CONNECTION_POOL] Error de compatibilidad SQLAlchemy 2.0.44 + Python 3.13 detectado. "
                    f"Connection pooling desactivado automáticamente (fallback seguro). "
                    f"El sistema funcionará con conexiones directas sin problemas. "
                    f"Para resolver: Actualizar SQLAlchemy a versión >= 2.0.36 o usar Python 3.12."
                )
            else:
                logger.warning(
                    f"[CONNECTION_POOL] Error importando SQLAlchemy: {error_str[:200]}. "
                    "Connection pooling desactivado."
                )
            _pool_enabled = False
            return
        
        _pool_enabled = True
        
        # Pool para conexión ADMIN (fija)
        admin_conn_str = (
            f"mssql+pyodbc://{quote_plus(settings.DB_ADMIN_USER)}:"
            f"{quote_plus(settings.DB_ADMIN_PASSWORD)}@"
            f"{settings.DB_ADMIN_SERVER}:{settings.DB_ADMIN_PORT}/"
            f"{settings.DB_ADMIN_DATABASE}?"
            f"driver={quote_plus(settings.DB_DRIVER)}&"
            f"TrustServerCertificate=yes"
        )
        
        _pools['admin'] = create_engine(
            admin_conn_str,
            poolclass=QueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,  # Verificar conexiones antes de usar
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            echo=False
        )
        
        logger.info(
            f"[CONNECTION_POOL] Pool ADMIN inicializado. "
            f"Size={settings.DB_POOL_SIZE}, MaxOverflow={settings.DB_MAX_OVERFLOW}"
        )
        logger.info(
            f"[CONNECTION_POOL] Configuración de pools de tenants: "
            f"MaxPools={MAX_TENANT_POOLS}, PoolSize={TENANT_POOL_SIZE}, "
            f"MaxOverflow={TENANT_POOL_MAX_OVERFLOW}, InactivityTimeout={POOL_INACTIVITY_TIMEOUT}s"
        )
        
        # Pool para conexiones DEFAULT (tenant-aware) se crea dinámicamente
        # porque cada tenant puede tener su propia BD
        
    except (AssertionError, ImportError, AttributeError, Exception) as e:
        # ✅ CORRECCIÓN: Capturar error específico de Python 3.13
        error_str = str(e)
        if "TypingOnly" in error_str or "SQLCoreOperations" in error_str:
            logger.warning(
                f"[CONNECTION_POOL] Error de compatibilidad SQLAlchemy 2.0.44 + Python 3.13 detectado. "
                f"Connection pooling desactivado automáticamente (fallback seguro). "
                f"El sistema funcionará con conexiones directas sin problemas. "
                f"Para resolver: Actualizar SQLAlchemy o usar Python 3.12."
            )
        elif isinstance(e, ImportError):
            logger.warning(
                "[CONNECTION_POOL] SQLAlchemy no instalado. "
                "Instalar con: pip install sqlalchemy. "
                "Connection pooling desactivado automáticamente."
            )
        else:
            logger.warning(
                f"[CONNECTION_POOL] Error importando SQLAlchemy: {error_str[:200]}. "
                "Connection pooling desactivado."
            )
        _pool_enabled = False
    except Exception as e:
        logger.error(
            f"[CONNECTION_POOL] Error al inicializar pools: {str(e)}. "
            "Connection pooling desactivado (fallback seguro)",
            exc_info=True
        )
        _pool_enabled = False

# Inicializar al importar
_initialize_pools()


def _cleanup_inactive_pools():
    """
    Limpia pools inactivos usando estrategia LRU (Least Recently Used).
    
    ✅ CORRECCIÓN: Evita acumulación de pools sin uso.
    """
    global _pools, _pool_access_times
    
    if not _pool_enabled:
        return
    
    current_time = datetime.now()
    pools_to_remove = []
    
    # Identificar pools inactivos
    for pool_key, last_access in list(_pool_access_times.items()):
        if pool_key == 'admin':  # No cerrar pool ADMIN
            continue
        
        inactivity_duration = (current_time - last_access).total_seconds()
        if inactivity_duration > POOL_INACTIVITY_TIMEOUT:
            pools_to_remove.append(pool_key)
    
    # Cerrar pools inactivos
    for pool_key in pools_to_remove:
        try:
            pool_engine = _pools.get(pool_key)
            if pool_engine:
                pool_engine.dispose()
                logger.info(
                    f"[CONNECTION_POOL] Pool inactivo cerrado: {pool_key} "
                    f"(inactivo por {POOL_INACTIVITY_TIMEOUT}s)"
                )
            del _pools[pool_key]
            del _pool_access_times[pool_key]
        except Exception as e:
            logger.warning(f"[CONNECTION_POOL] Error cerrando pool inactivo {pool_key}: {e}")


def _evict_oldest_pool():
    """
    Elimina el pool más antiguo (LRU) cuando se alcanza el límite máximo.
    
    ✅ CORRECCIÓN: Evita crear más pools de los permitidos.
    """
    global _pools, _pool_access_times
    
    if not _pool_access_times:
        return
    
    # El primer elemento en OrderedDict es el más antiguo (LRU)
    oldest_pool_key = next(iter(_pool_access_times))
    
    if oldest_pool_key == 'admin':  # No cerrar pool ADMIN
        # Si el más antiguo es ADMIN, buscar el siguiente
        if len(_pool_access_times) > 1:
            oldest_pool_key = list(_pool_access_times.keys())[1]
        else:
            return
    
    try:
        pool_engine = _pools.get(oldest_pool_key)
        if pool_engine:
            pool_engine.dispose()
            logger.info(
                f"[CONNECTION_POOL] Pool evictado (límite alcanzado): {oldest_pool_key}"
            )
        del _pools[oldest_pool_key]
        del _pool_access_times[oldest_pool_key]
    except Exception as e:
        logger.warning(f"[CONNECTION_POOL] Error evictando pool {oldest_pool_key}: {e}")


def _get_pool_for_tenant(client_id: int, connection_string: str) -> Any:
    """
    Obtiene o crea un pool para un tenant específico.
    
    ✅ FASE 0: Límites aumentados para soportar 100+ tenants dedicados.
    ✅ FASE 3: Optimizado con estructura modular y mejor gestión de recursos.
    
    Los pools se crean dinámicamente porque cada tenant puede tener su propia BD.
    Estrategia:
    1. Si el pool existe, actualizar tiempo de acceso (LRU)
    2. Si no existe y hay espacio, crear nuevo pool
    3. Si no hay espacio, evictar pool más antiguo (LRU)
    4. Limpiar pools inactivos periódicamente
    
    Optimizaciones FASE 3:
    - Límites aumentados (200 pools máximo)
    - Timeout reducido para limpieza más agresiva (30 min)
    - Pool size optimizado (5 conexiones base + 3 overflow)
    """
    global _pools, _pool_access_times
    
    if not _pool_enabled:
        return None
    
    try:
        # ✅ CORRECCIÓN: Import defensivo (mismo que en _initialize_pools)
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from sqlalchemy import create_engine, pool
            from sqlalchemy.pool import QueuePool
            from urllib.parse import quote_plus
        
        # Crear clave única para el pool
        pool_key = f"tenant_{client_id}"
        
        # Si ya existe, actualizar tiempo de acceso y retornarlo
        if pool_key in _pools:
            # Mover al final (más reciente) en OrderedDict
            _pool_access_times.move_to_end(pool_key)
            _pool_access_times[pool_key] = datetime.now()
            return _pools[pool_key]
        
        # ✅ CORRECCIÓN: Limpiar pools inactivos antes de crear uno nuevo
        _cleanup_inactive_pools()
        
        # ✅ CORRECCIÓN: Verificar límite de pools antes de crear
        tenant_pools_count = len([k for k in _pools.keys() if k.startswith('tenant_')])
        if tenant_pools_count >= MAX_TENANT_POOLS:
            logger.warning(
                f"[CONNECTION_POOL] Límite de pools alcanzado ({MAX_TENANT_POOLS}). "
                f"Evictando pool más antiguo..."
            )
            _evict_oldest_pool()
        
        # Convertir connection string de pyodbc a SQLAlchemy
        conn_parts = {}
        for part in connection_string.split(';'):
            if '=' in part:
                key, value = part.split('=', 1)
                conn_parts[key.strip()] = value.strip()
        
        # Construir connection string de SQLAlchemy
        driver = conn_parts.get('DRIVER', settings.DB_DRIVER).strip('{}')
        server = conn_parts.get('SERVER', '')
        database = conn_parts.get('DATABASE', '')
        uid = conn_parts.get('UID', '')
        pwd = conn_parts.get('PWD', '')
        
        # Extraer servidor y puerto
        if ',' in server:
            server, port = server.split(',')
        else:
            port = "1433"
        
        sqlalchemy_conn_str = (
            f"mssql+pyodbc://{quote_plus(uid)}:"
            f"{quote_plus(pwd)}@"
            f"{server}:{port}/"
            f"{database}?"
            f"driver={quote_plus(driver)}&"
            f"TrustServerCertificate=yes"
        )
        
        # ✅ FASE 0: Pool size optimizado para escalabilidad (5 base + 3 overflow)
        # ✅ FASE 3: Configuración balanceada para soportar 100+ tenants
        pool_engine = create_engine(
            sqlalchemy_conn_str,
            poolclass=QueuePool,
            pool_size=TENANT_POOL_SIZE,  # Optimizado: 5 conexiones base
            max_overflow=TENANT_POOL_MAX_OVERFLOW,  # Optimizado: 3 conexiones overflow
            pool_pre_ping=True,  # Verificar conexiones antes de usar
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            echo=False
        )
        
        _pools[pool_key] = pool_engine
        _pool_access_times[pool_key] = datetime.now()
        
        tenant_pools_count = len([k for k in _pools.keys() if k.startswith('tenant_')])
        logger.info(
            f"[CONNECTION_POOL] Pool creado para tenant {client_id}. "
            f"BD: {database}, Pools activos: {tenant_pools_count}/{MAX_TENANT_POOLS}, "
            f"Pool size: {TENANT_POOL_SIZE}+{TENANT_POOL_MAX_OVERFLOW}"
        )
        
        return pool_engine
        
    except Exception as e:
        logger.error(
            f"[CONNECTION_POOL] Error creando pool para tenant {client_id}: {str(e)}",
            exc_info=True
        )
        return None


def get_connection_from_pool(
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[int] = None,
    connection_string: Optional[str] = None
) -> Optional[Any]:
    """
    Obtiene una conexión del pool (si está habilitado).
    
    ✅ FASE 2: Connection pooling con fallback
    - Si pooling está activo, retorna conexión del pool (SQLAlchemy connection)
    - Si no, retorna None (se usará conexión directa)
    
    IMPORTANTE: La conexión retornada es de SQLAlchemy, no pyodbc directamente.
    Para obtener la conexión pyodbc raw, usar: connection.connection.driver_connection
    
    Args:
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente (para DEFAULT, tenant-aware)
        connection_string: Connection string (para crear pool dinámico)
    
    Returns:
        SQLAlchemy connection o None si pooling no está disponible
    """
    if not _pool_enabled:
        return None
    
    try:
        if connection_type == DatabaseConnection.ADMIN:
            # Pool ADMIN (fijo)
            if 'admin' in _pools:
                return _pools['admin'].connect()
        else:
            # Pool DEFAULT (tenant-aware, dinámico)
            if client_id and connection_string:
                pool_engine = _get_pool_for_tenant(client_id, connection_string)
                if pool_engine:
                    return pool_engine.connect()
        
        return None
        
    except Exception as e:
        logger.warning(
            f"[CONNECTION_POOL] Error obteniendo conexión del pool: {str(e)}. "
            "Usando conexión directa (fallback)"
        )
        return None


def is_pooling_enabled() -> bool:
    """Verifica si connection pooling está habilitado."""
    return _pool_enabled


def get_pool_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas de los pools activos.
    
    ✅ NUEVO: Útil para monitoreo y debugging.
    """
    tenant_pools = [k for k in _pools.keys() if k.startswith('tenant_')]
    
    return {
        "pooling_enabled": _pool_enabled,
        "total_pools": len(_pools),
        "tenant_pools": len(tenant_pools),
        "max_tenant_pools": MAX_TENANT_POOLS,
        "admin_pool": "admin" in _pools,
        "pool_keys": list(_pools.keys())
    }


def close_all_pools():
    """
    Cierra todos los pools (útil para shutdown).
    
    ✅ CORRECCIÓN: Manejo robusto de errores durante shutdown.
    Suprime errores de compatibilidad SQLAlchemy + Python 3.13 durante la limpieza.
    """
    global _pools, _pool_access_times
    
    # Si pooling no está habilitado, no hay nada que cerrar
    if not _pool_enabled:
        return
    
    try:
        # ✅ CORRECCIÓN: Suprimir warnings durante shutdown para evitar ruido en logs
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            for pool_key, pool_engine in list(_pools.items()):
                try:
                    pool_engine.dispose()
                    logger.debug(f"[CONNECTION_POOL] Pool '{pool_key}' cerrado")
                except (AssertionError, AttributeError, ImportError) as e:
                    # Error conocido de compatibilidad SQLAlchemy 2.0.44 + Python 3.13
                    error_str = str(e)
                    if "TypingOnly" in error_str or "SQLCoreOperations" in error_str:
                        # Suprimir este error específico durante shutdown (es solo un warning)
                        logger.debug(
                            f"[CONNECTION_POOL] Pool '{pool_key}' cerrado "
                            f"(error de compatibilidad suprimido durante shutdown)"
                        )
                    else:
                        logger.warning(f"[CONNECTION_POOL] Error cerrando pool '{pool_key}': {e}")
                except Exception as e:
                    logger.warning(f"[CONNECTION_POOL] Error cerrando pool '{pool_key}': {e}")
        
        _pools.clear()
        _pool_access_times.clear()
        logger.info("[CONNECTION_POOL] Todos los pools cerrados")
        
    except (AssertionError, AttributeError, ImportError) as e:
        # ✅ CORRECCIÓN: Error conocido de compatibilidad durante shutdown
        error_str = str(e)
        if "TypingOnly" in error_str or "SQLCoreOperations" in error_str:
            # Este error ocurre durante la limpieza de módulos de Python
            # No es crítico, solo aparece en logs durante shutdown
            logger.debug(
                "[CONNECTION_POOL] Error de compatibilidad SQLAlchemy + Python 3.13 "
                "durante shutdown (puede ignorarse, no afecta funcionalidad)"
            )
        else:
            logger.warning(f"[CONNECTION_POOL] Error cerrando pools: {e}")
    except Exception as e:
        logger.warning(f"[CONNECTION_POOL] Error cerrando pools: {e}")


# ============================================
# LOGGING DE INICIALIZACIÓN
# ============================================

if _pool_enabled:
    logger.info("✅ Módulo de connection pooling cargado y activo")
    logger.info(
        f"   Configuración: MaxTenantPools={MAX_TENANT_POOLS}, "
        f"TenantPoolSize={TENANT_POOL_SIZE}, "
        f"InactivityTimeout={POOL_INACTIVITY_TIMEOUT}s"
    )
else:
    logger.info("ℹ️ Módulo de connection pooling cargado pero desactivado")
