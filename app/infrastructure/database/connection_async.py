# app/infrastructure/database/connection_async.py
"""
✅ FASE 2: Conexiones 100% ASYNC - Única fuente de conexiones a BD

- Implementa conexiones async usando SQLAlchemy AsyncEngine
- Usa aioodbc como driver async para SQL Server
- Reemplaza completamente connection.py (síncrono)

USO:
    # En funciones async
    async with get_db_connection() as session:
        result = await session.execute(select(UsuarioTable))
        rows = result.fetchall()
"""

import logging
from typing import AsyncIterator, Optional, Union
from contextlib import asynccontextmanager
from enum import Enum
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.core.tenant.context import get_current_client_id

logger = logging.getLogger(__name__)

# ============================================================================
# ENUM: DatabaseConnection
# ============================================================================
class DatabaseConnection(Enum):
    """Tipo de conexión a base de datos."""
    DEFAULT = "default"  # Conexión tenant-aware
    ADMIN = "admin"       # Conexión de administración (metadata)

# Cache de engines async (uno por tenant)
_async_engines: dict[str, any] = {}

# Verificar dependencias async (obligatorias en FASE 2)
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    from urllib.parse import quote_plus
    ASYNC_AVAILABLE = True
    logger.info("[ASYNC_CONNECTION] SQLAlchemy async disponible")
except ImportError as e:
    ASYNC_AVAILABLE = False
    logger.error(f"[ASYNC_CONNECTION] SQLAlchemy async NO disponible: {e}")
    logger.error("[ASYNC_CONNECTION] CRÍTICO: Instalar: pip install 'sqlalchemy[asyncio]' aioodbc")
    raise ImportError(
        "SQLAlchemy async es obligatorio en FASE 2. "
        "Instalar: pip install 'sqlalchemy[asyncio]' aioodbc"
    )

try:
    import aioodbc
    AIOODBC_AVAILABLE = True
    logger.info("[ASYNC_CONNECTION] aioodbc disponible")
except ImportError:
    AIOODBC_AVAILABLE = False
    logger.error("[ASYNC_CONNECTION] aioodbc NO disponible")
    logger.error("[ASYNC_CONNECTION] CRÍTICO: Instalar: pip install aioodbc")
    raise ImportError(
        "aioodbc es obligatorio en FASE 2. "
        "Instalar: pip install aioodbc"
    )


async def _get_connection_metadata_async(client_id: int) -> dict:
    """
    Obtiene metadata de conexión para un cliente (async).
    
    ✅ FASE 2: Versión async que reemplaza la función síncrona.
    
    Args:
        client_id: ID del cliente
    
    Returns:
        Dict con metadata de conexión
    """
    # Importar aquí para evitar circular
    from app.core.tenant.routing import get_connection_metadata
    
    # Por ahora, usar la función síncrona (será refactorizada en FASE 2 completa)
    # TODO: Refactorizar get_connection_metadata() para ser async
    return get_connection_metadata(client_id)


def _build_async_connection_string(
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[Union[int, UUID]] = None,
    connection_metadata: Optional[dict] = None
) -> str:
    """
    Construye el connection string async para SQLAlchemy.
    
    ✅ FASE 2: Refactorizado para no depender de routing.py síncrono.
    
    Args:
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente (opcional, usa contexto si no se proporciona)
        connection_metadata: Metadata de conexión (opcional, evita consulta adicional)
    
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
                    detail="No se pudo obtener cliente_id del contexto para conexión async",
                    internal_code="CLIENT_ID_MISSING"
                )
        
        # Si no se proporciona metadata, construir desde settings (Single-DB por defecto)
        if connection_metadata:
            database_type = connection_metadata.get("database_type", "single")
            tipo_instalacion = connection_metadata.get("tipo_instalacion", "shared")
            
            if database_type == "multi":
                # Multi-DB: usar metadata
                servidor = connection_metadata.get("servidor")
                puerto = connection_metadata.get("puerto", 1433)
                nombre_bd = connection_metadata.get("nombre_bd")
                usuario = connection_metadata.get("usuario")
                password = connection_metadata.get("password")
                
                # ✅ CRÍTICO: Para clientes dedicated, NO hacer fallback a Single-DB
                # Si faltan credenciales, lanzar error claro
                if not all([servidor, nombre_bd, usuario, password]):
                    error_msg = (
                        f"Cliente {client_id} es '{tipo_instalacion}' (requiere BD dedicada) pero "
                        f"las credenciales de conexión no están disponibles o no se pueden desencriptar. "
                        f"Verificar: 1) Registro en cliente_conexion con es_activo=1, "
                        f"2) Credenciales encriptadas correctamente, "
                        f"3) ENCRYPTION_KEY correcta en .env"
                    )
                    logger.error(f"[CONN_STR] {error_msg}")
                    logger.error(
                        f"[CONN_STR] Metadata recibida: servidor={servidor}, "
                        f"bd={nombre_bd}, usuario={'***' if usuario else None}, "
                        f"password={'***' if password else None}"
                    )
                    raise DatabaseError(
                        detail=error_msg,
                        internal_code="DEDICATED_DB_CREDENTIALS_MISSING"
                    )
                
                return (
                    f"mssql+aioodbc://{quote_plus(str(usuario))}:"
                    f"{quote_plus(str(password))}@"
                    f"{servidor}:{puerto}/"
                    f"{nombre_bd}?"
                    f"driver={quote_plus(settings.DB_DRIVER)}&"
                    f"TrustServerCertificate=yes"
                )
        
        # Single-DB o fallback: usar settings
        return (
            f"mssql+aioodbc://{quote_plus(settings.DB_USER)}:"
            f"{quote_plus(settings.DB_PASSWORD)}@"
            f"{settings.DB_SERVER}:{settings.DB_PORT}/"
            f"{settings.DB_DATABASE}?"
            f"driver={quote_plus(settings.DB_DRIVER)}&"
            f"TrustServerCertificate=yes"
        )


def _get_async_engine(
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[Union[int, UUID]] = None,
    connection_metadata: Optional[dict] = None
) -> Optional[AsyncEngine]:
    """
    Obtiene o crea un AsyncEngine para la conexión especificada.
    
    ✅ FASE 2: Refactorizado para no depender de routing.py síncrono.
    
    Args:
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente (opcional, usa contexto si no se proporciona)
        connection_metadata: Metadata de conexión (opcional, evita consulta adicional)
    
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
        conn_str = _build_async_connection_string(connection_type, client_id, connection_metadata)
        
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
async def get_db_connection(
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[Union[int, UUID]] = None,
    connection_metadata: Optional[dict] = None
) -> AsyncIterator[AsyncSession]:
    """
    Context manager async para obtener y cerrar una conexión a BD.
    
    ✅ FASE 2: Única función de conexión (reemplaza get_db_connection síncrono).
    - Versión async que NO bloquea el event loop
    - Usa SQLAlchemy AsyncEngine + aioodbc
    
    Args:
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente (opcional, usa contexto si no se proporciona)
        connection_metadata: Metadata de conexión (opcional, evita consulta adicional)
    
    Yields:
        AsyncSession de SQLAlchemy
    
    Raises:
        DatabaseError: Si no se puede crear la conexión
        ImportError: Si las dependencias async no están instaladas
    
    Ejemplo:
        async with get_db_connection() as session:
            result = await session.execute(select(UsuarioTable))
            rows = result.fetchall()
    """
    if not ASYNC_AVAILABLE or not AIOODBC_AVAILABLE:
        raise ImportError(
            "Dependencias async no disponibles. "
            "Instalar: pip install 'sqlalchemy[asyncio]' aioodbc"
        )
    
    # ✅ FASE 5: Si no se proporciona metadata y es DEFAULT, obtenerla del routing
    if connection_type == DatabaseConnection.DEFAULT and not connection_metadata:
        if client_id is None:
            try:
                client_id = get_current_client_id()
            except RuntimeError:
                pass  # Continuar sin metadata
        
        if client_id:
            try:
                from app.core.tenant.routing import get_connection_metadata_async
                from uuid import UUID
                # Convertir client_id a UUID si es necesario
                if isinstance(client_id, int):
                    try:
                        client_id_uuid = UUID(int=client_id) if client_id > 0 else None
                    except (ValueError, OverflowError):
                        client_id_uuid = None
                elif isinstance(client_id, UUID):
                    client_id_uuid = client_id
                else:
                    client_id_uuid = None
                
                if client_id_uuid:
                    connection_metadata = await get_connection_metadata_async(client_id_uuid)
                    logger.debug(f"[ASYNC_CONNECTION] Metadata obtenida del routing para cliente {client_id}")
            except Exception as routing_err:
                logger.debug(f"[ASYNC_CONNECTION] No se pudo obtener metadata del routing: {routing_err}")
                # Continuar sin metadata (usará Single-DB por defecto)
    
    engine = _get_async_engine(connection_type, client_id, connection_metadata)
    
    if not engine:
        raise DatabaseError(
            detail="No se pudo crear AsyncEngine para la conexión",
            internal_code="ENGINE_CREATION_ERROR"
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


# Alias para compatibilidad (deprecated)
get_db_connection_async = get_db_connection


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

