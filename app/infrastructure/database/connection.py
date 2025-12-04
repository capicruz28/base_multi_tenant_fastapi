# app/infrastructure/database/connection.py
"""
⚠️ DEPRECATED: Este archivo está deprecated en FASE 2.

✅ FASE 2: Migrar a app/infrastructure/database/connection_async.py
- Todas las funciones ahora son async
- Usa SQLAlchemy AsyncSession + aioodbc
- Reemplaza completamente este archivo

Este archivo se mantiene temporalmente para compatibilidad durante la migración.
NO usar en código nuevo.
"""

import logging
from typing import Iterator, Optional
from enum import Enum

# ⚠️ DEPRECATED: Este archivo está deprecated, solo mantener imports mínimos
try:
    from app.core.config import settings
except ImportError:
    # Fallback si settings no está disponible
    settings = None

logger = logging.getLogger(__name__)

# ✅ FASE 2: Re-exportar DatabaseConnection desde connection_async
try:
    from app.infrastructure.database.connection_async import DatabaseConnection
except ImportError:
    # Fallback para compatibilidad
    class DatabaseConnection(Enum):
        DEFAULT = "default"
        ADMIN = "admin"

class DatabaseConnection(Enum):
    # DEFAULT ahora será tenant-aware
    DEFAULT = "default" 
    # ADMIN se mantiene para tareas que requieran acceso a la metadata o base de datos de administración
    ADMIN = "admin" 

def get_connection_string(connection_type: DatabaseConnection = DatabaseConnection.DEFAULT) -> str:
    """
    [DEPRECADO PARA DEFAULT] Obtiene la cadena de conexión según el tipo.
    Para DEFAULT, se recomienda usar get_db_connection que resuelve el tenant.
    """
    if connection_type == DatabaseConnection.ADMIN:
        # Conexión para administración (no tenant-aware)
        return (
            f"DRIVER={{{settings.DB_DRIVER}}};"
            f"SERVER={settings.DB_ADMIN_SERVER},{settings.DB_ADMIN_PORT};"
            f"DATABASE={settings.DB_ADMIN_DATABASE};"
            f"UID={settings.DB_ADMIN_USER};"
            f"PWD={settings.DB_ADMIN_PASSWORD};"
            "TrustServerCertificate=yes;"
        )
    else:
        # La conexión DEFAULT ya no se construye aquí, sino en multi_db.py.
        # Esto evita redundancia si se cambia la lógica de conexión de tenants.
        # Se retorna una conexión no tenant-aware (la principal) como fallback.
        return settings.get_database_url(is_admin=False)


# ⚠️ DEPRECATED: Usar connection_async.get_db_connection() en su lugar
def get_db_connection(connection_type: DatabaseConnection = DatabaseConnection.DEFAULT):
    """
    ⚠️ DEPRECATED: Esta función está deprecated en FASE 2.
    
    ✅ FASE 2: Migrar a app/infrastructure/database/connection_async.get_db_connection()
    
    Esta función mantiene compatibilidad temporal pero debe migrarse a async.
    """
    logger.error(
        "[DEPRECATED] get_db_connection() síncrono está deprecated. "
        "Migrar a connection_async.get_db_connection() (async)."
    )
    
    raise NotImplementedError(
        "get_db_connection() síncrono está deprecated. "
        "Usar connection_async.get_db_connection() (async) en su lugar."
    )
    conn = None
    pool_conn = None
    use_pool = False
    
    try:
        # ✅ FASE 2: Intentar usar pool primero (si está habilitado)
        if POOLING_AVAILABLE and is_pooling_enabled() and settings.ENABLE_CONNECTION_POOLING:
            try:
                if connection_type == DatabaseConnection.DEFAULT:
                    # Obtener client_id y connection string para pool
                    try:
                        client_id = get_current_client_id()
                        conn_str = get_client_db_connection_string(client_id)
                        
                        pool_conn = get_connection_from_pool(
                            connection_type=connection_type,
                            client_id=client_id,
                            connection_string=conn_str
                        )
                        
                        if pool_conn:
                            # Convertir conexión de SQLAlchemy a pyodbc
                            # SQLAlchemy connection tiene .connection.driver_connection que es pyodbc
                            try:
                                conn = pool_conn.connection.driver_connection
                                use_pool = True
                                logger.debug(
                                    f"[POOL] Conexión obtenida del pool para cliente {client_id} "
                                    f"(DEFAULT/TENANT)"
                                )
                            except AttributeError:
                                # Si no tiene driver_connection, intentar connection directamente
                                conn = pool_conn.connection
                                use_pool = True
                                logger.debug(
                                    f"[POOL] Conexión obtenida del pool para cliente {client_id} "
                                    f"(DEFAULT/TENANT - método alternativo)"
                                )
                    except RuntimeError:
                        # Sin contexto, usar conexión directa
                        logger.debug("[POOL] Sin contexto de tenant, usando conexión directa")
                else:
                    # Pool ADMIN
                    pool_conn = get_connection_from_pool(connection_type=connection_type)
                    if pool_conn:
                        try:
                            conn = pool_conn.connection.driver_connection
                        except AttributeError:
                            conn = pool_conn.connection
                        use_pool = True
                        logger.debug(f"[POOL] Conexión obtenida del pool ({connection_type.value})")
                        
            except Exception as pool_err:
                logger.warning(
                    f"[POOL] Error obteniendo conexión del pool: {pool_err}. "
                    "Usando conexión directa (fallback seguro)"
                )
                # Continuar con conexión directa (fallback)
        
        # ✅ FALLBACK: Conexión directa (comportamiento original)
        if not use_pool:
            if connection_type == DatabaseConnection.DEFAULT:
                # CRÍTICO: Usa la función tenant-aware
                conn = get_db_connection_for_current_tenant()
                logger.debug(
                    f"Conexión directa a BD (DEFAULT/TENANT) establecida. "
                    f"Cliente ID: {get_current_client_id() if POOLING_AVAILABLE else 'N/A'}"
                )
            else:
                # Conexión ADMIN (mantenemos la lógica original)
                conn_str = get_connection_string(connection_type)
                conn = pyodbc.connect(conn_str, timeout=30)
                logger.debug(f"Conexión directa a BD ({connection_type.value}) establecida.")
            
        yield conn

    except pyodbc.Error as e:
        logger.error(f"Error de conexión a la base de datos ({connection_type.value}): {str(e)}", exc_info=True)
        # Aseguramos un mensaje de error consistente
        raise DatabaseError(status_code=500, detail=f"Error de conexión: {str(e)}")

    except Exception as e:
        logger.error(f"Error general en la gestión de conexión: {str(e)}", exc_info=True)
        raise

    finally:
        if use_pool and pool_conn:
            # Si usamos pool, cerrar la conexión del pool (la devuelve al pool)
            try:
                pool_conn.close()  # Cierra la conexión del pool (la devuelve al pool)
                logger.debug(f"[POOL] Conexión devuelta al pool ({connection_type.value})")
            except Exception as e:
                logger.warning(f"[POOL] Error devolviendo conexión al pool: {e}")
        elif conn:
            # Conexión directa: cerrar normalmente
            try:
                conn.close()
                logger.debug(f"Conexión directa a BD ({connection_type.value}) cerrada.")
            except Exception as e:
                logger.warning(f"Error cerrando conexión directa: {e}")

# Asume que test_drivers está definido en alguna parte de tu código original, si no, añádelo:
# def test_drivers():
#     return pyodbc.drivers()