# app/infrastructure/database/connection_async.py
"""
Versión ASYNC de connection.py para operaciones no bloqueantes.

✅ CORRECCIÓN AUDITORÍA: Performance - I/O Síncrono
- Implementa conexiones async usando SQLAlchemy AsyncEngine
- Usa aioodbc como driver async para SQL Server
- Coexiste con connection.py (no reemplaza, permite migración gradual)

USO:
    # En funciones async
    async with get_db_connection_async() as conn:
        result = await conn.execute(text("SELECT * FROM usuario"))
        rows = result.fetchall()
"""

import logging
from typing import AsyncIterator, Optional
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.core.tenant.context import get_current_client_id
from app.core.tenant.routing import get_client_db_connection_string
from app.infrastructure.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

# ✅ FLAG: Habilitar/deshabilitar async (para migración gradual)
# Se verifica dinámicamente en get_db_connection_async()

# Cache de engines async (uno por tenant)
_async_engines: dict[str, any] = {}
_async_engines_lock = None  # Se inicializa si threading está disponible

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    from urllib.parse import quote_plus
    ASYNC_AVAILABLE = True
    logger.info("[ASYNC_CONNECTION] SQLAlchemy async disponible")
except ImportError as e:
    ASYNC_AVAILABLE = False
    logger.warning(f"[ASYNC_CONNECTION] SQLAlchemy async no disponible: {e}")
    logger.warning("[ASYNC_CONNECTION] Instalar: pip install 'sqlalchemy[asyncio]' aioodbc")

try:
    import aioodbc
    AIOODBC_AVAILABLE = True
    logger.info("[ASYNC_CONNECTION] aioodbc disponible")
except ImportError:
    AIOODBC_AVAILABLE = False
    logger.warning("[ASYNC_CONNECTION] aioodbc no disponible")
    logger.warning("[ASYNC_CONNECTION] Instalar: pip install aioodbc")


def _build_async_connection_string(
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[int] = None
) -> str:
    """
    Construye el connection string async para SQLAlchemy.
    
    Args:
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente (opcional, usa contexto si no se proporciona)
    
    Returns:
        Connection string para SQLAlchemy AsyncEngine
    """
    if connection_type == DatabaseConnection.ADMIN:
        # Conexión ADMIN
        return (
            f"mssql+aioodbc://{quote_plus(settings.DB_ADMIN_USER)}:"
            f"{quote_plus(settings.DB_ADMIN_PASSWORD)}@"
            f"{settings.DB_ADMIN_SERVER}:{settings.DB_ADMIN_PORT}/"
            f"{settings.DB_ADMIN_DATABASE}?"
            f"driver={quote_plus(settings.DB_DRIVER)}&"
            f"TrustServerCertificate=yes"
        )
    else:
        # Conexión DEFAULT (tenant-aware)
        if client_id is None:
            try:
                client_id = get_current_client_id()
            except RuntimeError:
                raise DatabaseError(
                    status_code=500,
                    detail="No se pudo obtener cliente_id del contexto para conexión async"
                )
        
        conn_str = get_client_db_connection_string(client_id)
        
        # Parsear connection string de pyodbc a formato SQLAlchemy async
        conn_parts = {}
        for part in conn_str.split(';'):
            if '=' in part:
                key, value = part.split('=', 1)
                conn_parts[key.strip()] = value.strip()
        
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
        
        return (
            f"mssql+aioodbc://{quote_plus(uid)}:"
            f"{quote_plus(pwd)}@"
            f"{server}:{port}/"
            f"{database}?"
            f"driver={quote_plus(driver)}&"
            f"TrustServerCertificate=yes"
        )


def _get_async_engine(
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[int] = None
) -> Optional[AsyncEngine]:
    """
    Obtiene o crea un AsyncEngine para la conexión especificada.
    
    Args:
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente (opcional, usa contexto si no se proporciona)
    
    Returns:
        AsyncEngine o None si no está disponible
    """
    if not ASYNC_AVAILABLE or not AIOODBC_AVAILABLE:
        return None
    
    # Crear clave única para el engine
    if connection_type == DatabaseConnection.ADMIN:
        engine_key = "admin"
    else:
        if client_id is None:
            try:
                client_id = get_current_client_id()
            except RuntimeError:
                logger.error("[ASYNC_CONNECTION] No se pudo obtener cliente_id del contexto")
                return None
        engine_key = f"tenant_{client_id}"
    
    # Si ya existe, retornarlo
    if engine_key in _async_engines:
        return _async_engines[engine_key]
    
    # Crear nuevo engine
    try:
        conn_str = _build_async_connection_string(connection_type, client_id)
        
        engine = create_async_engine(
            conn_str,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            echo=False
        )
        
        _async_engines[engine_key] = engine
        logger.info(f"[ASYNC_CONNECTION] AsyncEngine creado para {engine_key}")
        
        return engine
    except Exception as e:
        logger.error(f"[ASYNC_CONNECTION] Error creando AsyncEngine: {e}", exc_info=True)
        return None


@asynccontextmanager
async def get_db_connection_async(
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[int] = None
) -> AsyncIterator[AsyncSession]:
    """
    Context manager async para obtener y cerrar una conexión a BD.
    
    ✅ CORRECCIÓN AUDITORÍA: Versión async que NO bloquea el event loop.
    
    Args:
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente (opcional, usa contexto si no se proporciona)
    
    Yields:
        AsyncSession de SQLAlchemy
    
    Raises:
        DatabaseError: Si no se puede crear la conexión
        ImportError: Si las dependencias async no están instaladas
    """
    # Verificar si async está habilitado
    enable_async = getattr(settings, 'ENABLE_ASYNC_CONNECTIONS', False)
    if not enable_async:
        raise RuntimeError(
            "Conexiones async no están habilitadas. "
            "Configurar ENABLE_ASYNC_CONNECTIONS=true en .env"
        )
    
    if not ASYNC_AVAILABLE or not AIOODBC_AVAILABLE:
        raise ImportError(
            "Dependencias async no disponibles. "
            "Instalar: pip install 'sqlalchemy[asyncio]' aioodbc"
        )
    
    engine = _get_async_engine(connection_type, client_id)
    
    if not engine:
        raise DatabaseError(
            status_code=500,
            detail="No se pudo crear AsyncEngine para la conexión"
        )
    
    # Crear session factory
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"[ASYNC_CONNECTION] Error en sesión async: {e}", exc_info=True)
            raise
        finally:
            await session.close()


async def close_all_async_engines():
    """
    Cierra todos los AsyncEngines creados.
    
    Útil para cleanup al apagar la aplicación.
    """
    global _async_engines
    
    for engine_key, engine in _async_engines.items():
        try:
            await engine.dispose()
            logger.debug(f"[ASYNC_CONNECTION] AsyncEngine {engine_key} cerrado")
        except Exception as e:
            logger.warning(f"[ASYNC_CONNECTION] Error cerrando engine {engine_key}: {e}")
    
    _async_engines.clear()
    logger.info("[ASYNC_CONNECTION] Todos los AsyncEngines cerrados")

