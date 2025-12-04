"""
Gestión de múltiples conexiones de base de datos para arquitectura híbrida.

✅ FASE 5: Refactorizado para centralizar lógica de conexión por tenant.

ARQUITECTURA SOPORTADA:
- Single-DB: Todos los clientes en bd_sistema (tenant isolation por cliente_id)
- Multi-DB: Cada cliente en su propia BD (bd_cliente_acme, bd_cliente_innova, etc.)

FLUJO DE ROUTING:
1. Obtener cliente_id del contexto actual (TenantContext)
2. Consultar metadata en cliente_conexion (con cache)
3. Determinar database_type (single/multi)
4. Construir connection string apropiado
5. Retornar conexión async

FALLBACK:
- Si no hay metadata → Single-DB (bd_sistema)
- Si falla conexión Multi-DB → Single-DB (bd_sistema)
- Si cliente_id es SYSTEM → ADMIN connection

✅ FASE 5: Nueva función centralizada:
- get_connection_for_tenant(): Retorna AsyncSession context manager
- Centraliza toda la lógica de routing
- Elimina dependencia de conexiones globales
"""

import logging
import json
from typing import Dict, Any, Optional, AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from contextlib import asynccontextmanager
import pyodbc

from app.core.config import settings
from app.core.tenant.context import get_current_client_id
from app.core.security.encryption import decrypt_credential
from app.core.tenant.cache import connection_cache
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

# ============================================
# CONSTANTES
# ============================================

DEFAULT_DATABASE_TYPE = "single"
# Convertir SUPERADMIN_CLIENTE_ID de string a UUID
SYSTEM_CLIENT_ID = UUID(settings.SUPERADMIN_CLIENTE_ID) if settings.SUPERADMIN_CLIENTE_ID else None


# ============================================
# METADATA RESOLUTION
# ============================================

async def _query_connection_metadata_from_db_async(client_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Consulta DIRECTAMENTE la BD para obtener metadata de conexión (ASYNC).
    
    ✅ FASE 2: Versión async que reemplaza la función síncrona.
    
    IMPORTANTE: Usa conexión ADMIN para evitar import circular.
    Esta función NO debe llamar a get_db_connection() con DEFAULT.
    
    Args:
        client_id: ID del cliente
    
    Returns:
        Dict con metadata o None si no existe
    
    Estructura del dict retornado:
        {
            "database_type": "single" | "multi",
            "servidor": "localhost",
            "puerto": 1433,
            "nombre_bd": "bd_cliente_acme",
            "usuario": "decrypted_user",
            "password": "decrypted_pass",
            "tipo_bd": "sqlserver",
            "usa_ssl": False,
            "tipo_instalacion": "cloud"
        }
    """
    from app.infrastructure.database.connection_async import get_db_connection, DatabaseConnection
    from app.infrastructure.database.tables import ClienteConexionTable, ClienteTable
    from sqlalchemy import select, text
    
    # Query para obtener metadata de conexión usando SQLAlchemy Core
    query = select(
        ClienteConexionTable.c.conexion_id,
        ClienteConexionTable.c.servidor,
        ClienteConexionTable.c.puerto,
        ClienteConexionTable.c.nombre_bd,
        ClienteConexionTable.c.usuario_encriptado,
        ClienteConexionTable.c.password_encriptado,
        ClienteConexionTable.c.tipo_bd,
        ClienteConexionTable.c.usa_ssl,
        ClienteTable.c.tipo_instalacion,
        ClienteTable.c.metadata_json
    ).select_from(
        ClienteConexionTable.join(
            ClienteTable, 
            ClienteConexionTable.c.cliente_id == ClienteTable.c.cliente_id
        )
    ).where(
        ClienteConexionTable.c.cliente_id == client_id,
        ClienteConexionTable.c.es_activo == True,
        ClienteConexionTable.c.es_conexion_principal == True
    ).order_by(
        ClienteConexionTable.c.conexion_id.desc()
    )
    
    try:
        # CRÍTICO: Usar conexión ADMIN async
        async with get_db_connection(DatabaseConnection.ADMIN) as session:
            result = await session.execute(query)
            row = result.fetchone()
            
            if not row:
                logger.debug(f"[METADATA] No hay configuración de conexión para cliente {client_id}")
                return None
            
            # Parsear metadata_json
            metadata_json_str = row[9]
            try:
                metadata_json = json.loads(metadata_json_str) if metadata_json_str else {}
            except json.JSONDecodeError:
                logger.warning(f"[METADATA] metadata_json inválido para cliente {client_id}")
                metadata_json = {}
            
            # Obtener tipo_instalacion del cliente
            tipo_instalacion = row[8] or "shared"
            
            # ✅ LÓGICA CORREGIDA: Determinar database_type
            # Si tipo_instalacion=dedicated → siempre Multi-DB
            # Si tipo_instalacion=shared → siempre Single-DB
            # Si hay database_isolation en metadata_json, también respetarlo
            database_isolation = metadata_json.get("database_isolation", False)
            
            if tipo_instalacion == "dedicated":
                # Cliente dedicated siempre usa Multi-DB
                database_type = "multi"
                logger.debug(
                    f"[METADATA] Cliente {client_id} es 'dedicated' → database_type=multi"
                )
            elif tipo_instalacion == "shared":
                # Cliente shared siempre usa Single-DB
                database_type = "single"
                logger.debug(
                    f"[METADATA] Cliente {client_id} es 'shared' → database_type=single"
                )
            elif database_isolation:
                # Si tiene database_isolation=true en metadata → Multi-DB
                database_type = "multi"
                logger.debug(
                    f"[METADATA] Cliente {client_id} tiene database_isolation=true → database_type=multi"
                )
            else:
                # Por defecto, Single-DB
                database_type = "single"
                logger.debug(
                    f"[METADATA] Cliente {client_id} → database_type=single (por defecto)"
                )
            
            # Desencriptar credenciales
            try:
                usuario_encriptado = row[4]
                password_encriptado = row[5]
                
                usuario = decrypt_credential(usuario_encriptado) if usuario_encriptado else ""
                password = decrypt_credential(password_encriptado) if password_encriptado else ""
            except Exception as decrypt_err:
                logger.error(
                    f"[METADATA] Error al desencriptar credenciales para cliente {client_id}: {decrypt_err}"
                )
                # Fallback: retornar None para usar Single-DB
                return None
            
            metadata = {
                "database_type": database_type,
                "servidor": row[1],
                "puerto": row[2] or 1433,
                "nombre_bd": row[3],
                "usuario": usuario,
                "password": password,
                "tipo_bd": row[6] or "sqlserver",
                "usa_ssl": bool(row[7]),
                "tipo_instalacion": row[8] or "cloud",
                "metadata_json": metadata_json
            }
            
            logger.debug(
                f"[METADATA] Cliente {client_id}: database_type={database_type}, "
                f"bd={metadata['nombre_bd']}"
            )
            
            return metadata
            
    except Exception as e:
        logger.error(
            f"[METADATA] Error al consultar metadata para cliente {client_id}: {e}",
            exc_info=True
        )
        return None


# ⚠️ DEPRECATED: Mantener para compatibilidad temporal
def _query_connection_metadata_from_db(client_id: UUID) -> Optional[Dict[str, Any]]:
    """
    ⚠️ DEPRECATED: Esta función está deprecated en FASE 2.
    
    ✅ FASE 2: Migrar a _query_connection_metadata_from_db_async()
    
    Esta función mantiene compatibilidad temporal pero debe migrarse a async.
    """
    logger.warning(
        "[DEPRECATED] _query_connection_metadata_from_db() síncrono está deprecated. "
        "Migrar a _query_connection_metadata_from_db_async() (async)."
    )
    
    # Por ahora, mantener funcionalidad básica pero loggear advertencia
    # TODO: Eliminar completamente en FASE 2 completa
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Si estamos en un contexto async, usar la versión async
            raise RuntimeError(
                "Esta función síncrona no puede usarse en contexto async. "
                "Usar _query_connection_metadata_from_db_async() en su lugar."
            )
        else:
            # Si no hay loop, ejecutar async
            return loop.run_until_complete(_query_connection_metadata_from_db_async(client_id))
    except RuntimeError:
        # No hay loop, crear uno nuevo
        return asyncio.run(_query_connection_metadata_from_db_async(client_id))


async def get_connection_metadata_async(client_id: UUID) -> Dict[str, Any]:
    """
    Obtiene metadata de conexión para un cliente (con cache) - ASYNC.
    
    ✅ FASE 2: Versión async que reemplaza la función síncrona.
    
    Cache mejorado con Redis:
    - Intenta obtener de Redis primero (cache distribuido)
    - Si falla, usa cache en memoria (fallback)
    - Si no está en cache, consulta BD
    
    FLUJO:
    1. Intentar obtener del cache Redis
    2. Si no, intentar cache en memoria
    3. Si no está en cache, consultar BD
    4. Guardar en ambos caches
    5. Si falla o no existe → Fallback a Single-DB
    
    Args:
        client_id: ID del cliente
    
    Returns:
        Dict con metadata (siempre retorna algo, nunca None)
    
    Fallback garantizado:
        Si cualquier cosa falla, retorna metadata para Single-DB
    """
    # Caso especial: SYSTEM siempre usa Single-DB
    if SYSTEM_CLIENT_ID and client_id == SYSTEM_CLIENT_ID:
        logger.debug(f"[METADATA] Cliente {client_id} es SYSTEM, usando Single-DB")
        return {
            "database_type": "single",
            "nombre_bd": settings.DB_DATABASE,
            "tipo_instalacion": "cloud"
        }
    
    # ✅ FASE 2: Intentar obtener de Redis primero (cache distribuido)
    if settings.ENABLE_REDIS_CACHE:
        try:
            from app.infrastructure.cache.redis_cache import get_cached
            redis_cached = get_cached(f"connection_metadata:{client_id}")
            if redis_cached:
                logger.debug(f"[METADATA] Cache Redis HIT para cliente {client_id}")
                # También actualizar cache en memoria (para compatibilidad)
                connection_cache.set(client_id, redis_cached)
                return redis_cached
        except Exception as e:
            logger.debug(f"[METADATA] Redis no disponible, usando cache en memoria: {e}")
    
    # Fallback: Intentar obtener del cache en memoria
    cached_metadata = connection_cache.get(client_id)
    
    if cached_metadata:
        logger.debug(f"[METADATA] Cache en memoria HIT para cliente {client_id}")
        return cached_metadata
    
    # Si no está en cache, consultar BD (async)
    logger.debug(f"[METADATA] Cache MISS para cliente {client_id}, consultando BD")
    metadata = await _query_connection_metadata_from_db_async(client_id)
    
    if metadata:
        # Guardar en ambos caches
        connection_cache.set(client_id, metadata)
        
        if settings.ENABLE_REDIS_CACHE:
            try:
                from app.infrastructure.cache.redis_cache import set_cached
                set_cached(f"connection_metadata:{client_id}", metadata, ttl=3600)
            except Exception as e:
                logger.debug(f"[METADATA] Redis no disponible para guardar: {e}")
        
        return metadata
    
    # Fallback: Determinar database_type basándose en tipo_instalacion
    # ✅ Obtener tipo_instalacion del cliente directamente
    tipo_instalacion_fallback = "shared"
    database_type_fallback = "single"
    
    try:
        from app.infrastructure.database.connection_async import get_db_connection, DatabaseConnection
        from app.infrastructure.database.tables import ClienteTable
        from sqlalchemy import select
        
        query_cliente = select(
            ClienteTable.c.tipo_instalacion
        ).where(
            ClienteTable.c.cliente_id == client_id
        )
        
        async with get_db_connection(DatabaseConnection.ADMIN) as session:
            result = await session.execute(query_cliente)
            row = result.fetchone()
            if row and row[0]:
                tipo_instalacion_fallback = row[0]
                logger.debug(
                    f"[METADATA] tipo_instalacion obtenido del cliente: {tipo_instalacion_fallback}"
                )
                
                # ✅ LÓGICA: Si tipo_instalacion es 'dedicated', debe usar Multi-DB
                # Intentar buscar cualquier conexión del cliente (no solo principal)
                if tipo_instalacion_fallback == "dedicated":
                    from app.infrastructure.database.tables import ClienteConexionTable
                    query_conexion = select(
                        ClienteConexionTable.c.conexion_id,
                        ClienteConexionTable.c.servidor,
                        ClienteConexionTable.c.puerto,
                        ClienteConexionTable.c.nombre_bd,
                        ClienteConexionTable.c.usuario_encriptado,
                        ClienteConexionTable.c.password_encriptado,
                        ClienteConexionTable.c.tipo_bd,
                        ClienteConexionTable.c.usa_ssl,
                        ClienteTable.c.tipo_instalacion,
                        ClienteTable.c.metadata_json
                    ).select_from(
                        ClienteConexionTable.join(
                            ClienteTable,
                            ClienteConexionTable.c.cliente_id == ClienteTable.c.cliente_id
                        )
                    ).where(
                        ClienteConexionTable.c.cliente_id == client_id,
                        ClienteConexionTable.c.es_activo == True
                    ).order_by(
                        ClienteConexionTable.c.es_conexion_principal.desc(),  # Priorizar principal
                        ClienteConexionTable.c.conexion_id.desc()
                    ).limit(1)
                    
                    result_conexion = await session.execute(query_conexion)
                    row_conexion = result_conexion.fetchone()
                    
                    if row_conexion:
                        # Hay conexión, procesarla como metadata completa
                        try:
                            metadata_json_str = row_conexion[9]
                            try:
                                metadata_json = json.loads(metadata_json_str) if metadata_json_str else {}
                            except json.JSONDecodeError:
                                metadata_json = {}
                            
                            # ✅ Para dedicated, siempre usar Multi-DB
                            database_type_fallback = "multi"
                            
                            # Desencriptar credenciales
                            usuario = None
                            password = None
                            try:
                                usuario_encriptado = row_conexion[4]
                                password_encriptado = row_conexion[5]
                                
                                usuario = decrypt_credential(usuario_encriptado) if usuario_encriptado else ""
                                password = decrypt_credential(password_encriptado) if password_encriptado else ""
                            except Exception as decrypt_err:
                                logger.error(
                                    f"[METADATA] Error al desencriptar credenciales para cliente {client_id}: {decrypt_err}"
                                )
                                # Si falla la desencriptación, no podemos usar esta conexión
                                # Saltar al siguiente paso (usar fallback)
                                usuario = None
                                password = None
                            
                            # Si se desencriptó correctamente, retornar metadata completa
                            if usuario and password:
                                metadata_completa = {
                                    "database_type": database_type_fallback,
                                    "servidor": row_conexion[1],
                                    "puerto": row_conexion[2] or 1433,
                                    "nombre_bd": row_conexion[3],
                                    "usuario": usuario,
                                    "password": password,
                                    "tipo_bd": row_conexion[6] or "sqlserver",
                                    "usa_ssl": bool(row_conexion[7]),
                                    "tipo_instalacion": tipo_instalacion_fallback,
                                    "metadata_json": metadata_json
                                }
                                
                                logger.info(
                                    f"[METADATA] Cliente {client_id} (dedicated) - metadata obtenida de conexión secundaria: "
                                    f"db_type={database_type_fallback}, bd={metadata_completa['nombre_bd']}"
                                )
                                
                                # Guardar en cache
                                connection_cache.set(client_id, metadata_completa)
                                if settings.ENABLE_REDIS_CACHE:
                                    try:
                                        from app.infrastructure.cache.redis_cache import set_cached
                                        set_cached(f"connection_metadata:{client_id}", metadata_completa, ttl=3600)
                                    except Exception:
                                        pass
                                
                                return metadata_completa
                            else:
                                logger.warning(
                                    f"[METADATA] Credenciales vacías o no desencriptables para cliente {client_id}"
                                )
                        except Exception as e:
                            logger.warning(
                                f"[METADATA] Error procesando conexión para cliente dedicated {client_id}: {e}"
                            )
                    
                    # Si es dedicated pero no hay conexión válida o las credenciales fallan
                    # Mantener database_type=multi pero sin credenciales (el sistema intentará conectar y fallará con error claro)
                    database_type_fallback = "multi"
                    logger.error(
                        f"[METADATA] ⚠️ CRÍTICO: Cliente {client_id} es 'dedicated' pero: "
                        f"1) No tiene conexión activa en cliente_conexion, O "
                        f"2) Las credenciales no se pueden desencriptar. "
                        f"El sistema intentará usar Multi-DB pero fallará sin credenciales válidas. "
                        f"Verificar: 1) Registro en cliente_conexion con es_activo=1, "
                        f"2) Credenciales encriptadas correctamente, "
                        f"3) ENCRYPTION_KEY correcta en .env"
                    )
                elif tipo_instalacion_fallback in ["shared", "onpremise", "hybrid"]:
                    # Para shared/onpremise/hybrid, usar Single-DB por defecto
                    database_type_fallback = "single"
    except Exception as e:
        logger.warning(
            f"[METADATA] Error al obtener tipo_instalacion del cliente {client_id}: {e}. "
            f"Usando 'shared' y Single-DB por defecto."
        )
    
    logger.warning(
        f"[METADATA] No se encontró metadata para cliente {client_id}. "
        f"Usando {database_type_fallback.upper()}-DB como fallback. "
        f"tipo_instalacion={tipo_instalacion_fallback}"
    )
    # ✅ CRÍTICO: Para clientes dedicated sin credenciales, NO incluir nombre_bd=None
    # Esto hará que el sistema falle con error claro en lugar de hacer fallback silencioso
    fallback_metadata = {
        "database_type": database_type_fallback,
        "nombre_bd": settings.DB_DATABASE if database_type_fallback == "single" else None,
        "tipo_instalacion": tipo_instalacion_fallback,
        "servidor": None if database_type_fallback == "multi" else None,
        "puerto": None if database_type_fallback == "multi" else None,
        "usuario": None if database_type_fallback == "multi" else None,
        "password": None if database_type_fallback == "multi" else None
    }
    
    # Guardar fallback en cache para evitar consultas repetidas
    connection_cache.set(client_id, fallback_metadata)
    return fallback_metadata


# ⚠️ DEPRECATED: Mantener para compatibilidad temporal
def get_connection_metadata(client_id: UUID) -> Dict[str, Any]:
    """
    ⚠️ DEPRECATED: Esta función está deprecated en FASE 2.
    
    ✅ FASE 2: Migrar a get_connection_metadata_async()
    
    Esta función mantiene compatibilidad temporal pero debe migrarse a async.
    """
    logger.warning(
        "[DEPRECATED] get_connection_metadata() síncrono está deprecated. "
        "Migrar a get_connection_metadata_async() (async)."
    )
    
    # Por ahora, mantener funcionalidad básica pero loggear advertencia
    # TODO: Eliminar completamente en FASE 2 completa
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Si estamos en un contexto async, usar la versión async
            raise RuntimeError(
                "Esta función síncrona no puede usarse en contexto async. "
                "Usar get_connection_metadata_async() en su lugar."
            )
        else:
            # Si no hay loop, ejecutar async
            return loop.run_until_complete(get_connection_metadata_async(client_id))
    except RuntimeError:
        # No hay loop, crear uno nuevo
        return asyncio.run(get_connection_metadata_async(client_id))


# ============================================
# CONNECTION STRING BUILDERS
# ============================================

def _build_single_db_connection_string() -> str:
    """
    Construye connection string para Single-DB (bd_sistema).
    
    Returns:
        Connection string completo
    """
    conn_str = (
        f"DRIVER={{{settings.DB_DRIVER}}};"
        f"SERVER={settings.DB_SERVER},{settings.DB_PORT};"
        f"DATABASE={settings.DB_DATABASE};"
        f"UID={settings.DB_USER};"
        f"PWD={settings.DB_PASSWORD};"
        "TrustServerCertificate=yes;"
    )
    
    logger.debug(
        f"[CONN_STR] Single-DB: SERVER={settings.DB_SERVER}, "
        f"DB={settings.DB_DATABASE}"
    )
    
    return conn_str


def _build_multi_db_connection_string(metadata: Dict[str, Any]) -> str:
    """
    Construye connection string para Multi-DB (BD dedicada del cliente).
    
    Args:
        metadata: Dict con información de conexión
    
    Returns:
        Connection string completo
    """
    servidor = metadata.get("servidor")
    puerto = metadata.get("puerto", 1433)
    nombre_bd = metadata.get("nombre_bd")
    usuario = metadata.get("usuario")
    password = metadata.get("password")
    usa_ssl = metadata.get("usa_ssl", False)
    
    # Validar campos requeridos
    if not all([servidor, nombre_bd, usuario, password]):
        raise ValueError(
            f"Metadata incompleta para Multi-DB: "
            f"servidor={servidor}, bd={nombre_bd}, "
            f"usuario={'***' if usuario else None}"
        )
    
    conn_str = (
        f"DRIVER={{{settings.DB_DRIVER}}};"
        f"SERVER={servidor},{puerto};"
        f"DATABASE={nombre_bd};"
        f"UID={usuario};"
        f"PWD={password};"
        f"TrustServerCertificate={'no' if usa_ssl else 'yes'};"
    )
    
    logger.debug(
        f"[CONN_STR] Multi-DB: SERVER={servidor}, "
        f"DB={nombre_bd}, USER={usuario[:3]}***"
    )
    
    return conn_str


def get_client_db_connection_string(client_id: UUID) -> str:
    """
    Determina y retorna la cadena de conexión apropiada para un cliente.
    
    ROUTING LOGIC:
    - Si database_type == "single" → bd_sistema
    - Si database_type == "multi" → BD dedicada del cliente
    - Si falla Multi-DB → Fallback a Single-DB
    
    Args:
        client_id: ID del cliente
    
    Returns:
        Connection string completo
    
    Raises:
        DatabaseError: Si no se puede construir ninguna connection string
    """
    try:
        # Obtener metadata (con cache y fallback integrado)
        metadata = get_connection_metadata(client_id)
        
        database_type = metadata.get("database_type", DEFAULT_DATABASE_TYPE)
        
        if database_type == "single":
            # Ruta Single-DB
            logger.debug(f"[ROUTING] Cliente {client_id} -> Single-DB (bd_sistema)")
            return _build_single_db_connection_string()
            
        elif database_type == "multi":
            # Ruta Multi-DB
            nombre_bd = metadata.get("nombre_bd", "UNKNOWN")
            logger.info(f"[ROUTING] Cliente {client_id} -> Multi-DB ({nombre_bd})")
            
            try:
                return _build_multi_db_connection_string(metadata)
            except Exception as build_err:
                # Fallback a Single-DB si falla construcción
                logger.error(
                    f"[ROUTING] Error al construir conn_str Multi-DB para cliente {client_id}: {build_err}. "
                    f"Usando Single-DB como fallback.",
                    exc_info=True
                )
                return _build_single_db_connection_string()
        
        else:
            # Tipo desconocido → Fallback
            logger.warning(
                f"[ROUTING] database_type desconocido '{database_type}' para cliente {client_id}. "
                f"Usando Single-DB."
            )
            return _build_single_db_connection_string()
            
    except Exception as e:
        # Fallback de emergencia
        logger.error(
            f"[ROUTING] Error crítico al determinar conexión para cliente {client_id}: {e}. "
            f"Usando Single-DB como último recurso.",
            exc_info=True
        )
        return _build_single_db_connection_string()


def get_db_connection_for_client(client_id: UUID) -> pyodbc.Connection:
    """
    Obtiene la conexión pyodbc para un cliente específico (sin usar contexto).
    
    IMPORTANTE: Esta función NO usa el contexto del tenant actual.
    Útil para Superadmin que necesita consultar datos de diferentes clientes.
    
    Args:
        client_id: ID del cliente para el cual obtener la conexión
    
    Returns:
        pyodbc.Connection configurada para el cliente especificado
    
    Raises:
        DatabaseError: Si falla la conexión a la BD
    
    Ejemplo:
        >>> conn = get_db_connection_for_client(2)  # Cliente específico
        >>> cursor = conn.cursor()
        >>> cursor.execute("SELECT * FROM usuario WHERE cliente_id = ?", (2,))
    """
    # Obtener connection string apropiado para el cliente especificado
    conn_str = get_client_db_connection_string(client_id)
    
    try:
        # Conectar
        conn = pyodbc.connect(conn_str, timeout=30)
        
        logger.debug(f"[TENANT_CONN] Conexión establecida para cliente {client_id} (sin contexto)")
        
        return conn
        
    except pyodbc.Error as db_err:
        logger.critical(
            f"[TENANT_CONN] Error CRÍTICO de conexión para cliente {client_id}: {db_err}",
            exc_info=True
        )
        raise DatabaseError(
            status_code=500,
            detail=f"Error al conectar a la base de datos del cliente {client_id}",
            internal_code="DB_CONNECTION_ERROR"
        )
    except Exception as e:
        logger.critical(
            f"[TENANT_CONN] Error inesperado al conectar para cliente {client_id}: {e}",
            exc_info=True
        )
        raise DatabaseError(
            status_code=500,
            detail="Error inesperado al conectar a la base de datos",
            internal_code="DB_CONNECTION_UNEXPECTED_ERROR"
        )


def get_db_connection_for_current_tenant() -> pyodbc.Connection:
    """
    Obtiene la conexión pyodbc para el cliente actual en el contexto.
    
    CONTEXTO REQUERIDO:
    - Debe ejecutarse dentro de un request con TenantMiddleware
    - Si se llama fuera de contexto → Usa SYSTEM_CLIENT_ID
    
    Returns:
        pyodbc.Connection configurada para el cliente actual
    
    Raises:
        DatabaseError: Si falla la conexión a la BD
    
    Ejemplo:
        >>> conn = get_db_connection_for_current_tenant()
        >>> cursor = conn.cursor()
        >>> cursor.execute("SELECT * FROM usuario WHERE cliente_id = ?", (client_id,))
    """
    try:
        # Intentar obtener el ID del contexto
        client_id = get_current_client_id()
    except RuntimeError:
        # Si falla (ej: script de fondo, inicialización), usar SYSTEM
        if SYSTEM_CLIENT_ID is None:
            raise ValueError(
                "SYSTEM_CLIENT_ID no está configurado. "
                "Configure SUPERADMIN_CLIENTE_ID en las variables de entorno."
            )
        logger.warning(
            "[TENANT_CONN] Llamada fuera de contexto de request. "
            f"Usando SYSTEM_CLIENT_ID={SYSTEM_CLIENT_ID}"
        )
        client_id = SYSTEM_CLIENT_ID
    
    # Usar la función genérica con el client_id del contexto
    return get_db_connection_for_client(client_id)


# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

def invalidate_client_connection_cache(client_id: UUID) -> bool:
    """
    Invalida el cache de metadata para un cliente específico.
    
    CUÁNDO USAR:
    - Después de actualizar cliente_conexion
    - Al cambiar database_type de un cliente
    - Al rotar credenciales
    
    Args:
        client_id: ID del cliente
    
    Returns:
        True si había entrada en cache, False si no
    
    Ejemplo:
        >>> # Después de actualizar configuración
        >>> invalidate_client_connection_cache(2)
        True
    """
    result = connection_cache.invalidate(client_id)
    
    if result:
        logger.info(f"[CACHE] Cache de metadata invalidado para cliente {client_id}")
    
    return result


def get_database_type(client_id: UUID) -> str:
    """
    Obtiene el tipo de BD de un cliente sin abrir conexión.
    
    Args:
        client_id: ID del cliente
    
    Returns:
        "single" o "multi"
    
    Ejemplo:
        >>> db_type = get_database_type(2)
        >>> print(f"Cliente 2 usa: {db_type}")
        Cliente 2 usa: multi
    """
    metadata = get_connection_metadata(client_id)
    return metadata.get("database_type", DEFAULT_DATABASE_TYPE)


# ============================================
# ✅ FASE 5: CONNECTION ROUTER CENTRALIZADO
# ============================================

@asynccontextmanager
async def get_connection_for_tenant(
    cliente_id: Optional[UUID] = None
) -> AsyncIterator[AsyncSession]:
    """
    ✅ FASE 5: Función centralizada para obtener conexión por tenant.
    
    Esta función centraliza toda la lógica de routing de conexiones:
    - Para superadmin: retorna conexión ADMIN
    - Para dedicated DBs: retorna conexión a BD dedicada
    - Para shared DBs: retorna conexión DEFAULT
    
    Args:
        cliente_id: ID del cliente (opcional, usa contexto si no se proporciona)
    
    Yields:
        AsyncSession de SQLAlchemy configurada para el tenant apropiado
    
    Raises:
        DatabaseError: Si no se puede crear la conexión
    
    Ejemplo:
        async with get_connection_for_tenant(cliente_id) as session:
            result = await session.execute(select(UsuarioTable))
            rows = result.fetchall()
    """
    from app.infrastructure.database.connection_async import (
        get_db_connection, DatabaseConnection
    )
    from app.core.config import settings
    
    # 1. Determinar cliente_id
    if cliente_id is None:
        try:
            from app.core.tenant.context import get_current_client_id
            cliente_id = get_current_client_id()
        except RuntimeError:
            # Sin contexto, usar SYSTEM
            if SYSTEM_CLIENT_ID:
                cliente_id = SYSTEM_CLIENT_ID
                logger.warning(
                    "[ROUTER] Sin contexto de tenant, usando SYSTEM_CLIENT_ID"
                )
            else:
                raise DatabaseError(
                    status_code=500,
                    detail="No se pudo determinar cliente_id para conexión"
                )
    
    # 2. Para superadmin, usar conexión ADMIN
    if SYSTEM_CLIENT_ID and cliente_id == SYSTEM_CLIENT_ID:
        logger.debug(f"[ROUTER] Cliente {cliente_id} es SuperAdmin, usando conexión ADMIN")
        async with get_db_connection(DatabaseConnection.ADMIN) as session:
            yield session
        return
    
    # 3. Obtener metadata de conexión (con cache)
    metadata = await get_connection_metadata_async(cliente_id)
    
    # 4. Determinar tipo de conexión
    database_type = metadata.get("database_type", DEFAULT_DATABASE_TYPE)
    
    if database_type == "multi":
        # Multi-DB: usar metadata para construir conexión dedicada
        logger.debug(
            f"[ROUTER] Cliente {cliente_id} -> Multi-DB ({metadata.get('nombre_bd')})"
        )
        # Pasar metadata a get_db_connection para que construya la conexión correcta
        async with get_db_connection(
            DatabaseConnection.DEFAULT,
            client_id=cliente_id,
            connection_metadata=metadata
        ) as session:
            yield session
    else:
        # Single-DB: usar conexión DEFAULT estándar
        logger.debug(f"[ROUTER] Cliente {cliente_id} -> Single-DB (bd_sistema)")
        async with get_db_connection(
            DatabaseConnection.DEFAULT,
            client_id=cliente_id
        ) as session:
            yield session


# ============================================
# LOGGING DE INICIALIZACIÓN
# ============================================

logger.info(
    f"Módulo multi_db cargado. "
    f"SYSTEM_CLIENT_ID={SYSTEM_CLIENT_ID}, "
    f"DEFAULT_TYPE={DEFAULT_DATABASE_TYPE}"
)