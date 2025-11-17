"""
Gestión de múltiples conexiones de base de datos para arquitectura híbrida.

ARQUITECTURA SOPORTADA:
- Single-DB: Todos los clientes en bd_sistema (tenant isolation por cliente_id)
- Multi-DB: Cada cliente en su propia BD (bd_cliente_acme, bd_cliente_innova, etc.)

FLUJO DE ROUTING:
1. Obtener cliente_id del contexto actual (TenantContext)
2. Consultar metadata en cliente_modulo_conexion (con cache)
3. Determinar database_type (single/multi)
4. Construir connection string apropiado
5. Retornar conexión

FALLBACK:
- Si no hay metadata → Single-DB (bd_sistema)
- Si falla conexión Multi-DB → Single-DB (bd_sistema)
- Si cliente_id es SYSTEM → bd_sistema
"""

import logging
import json
from typing import Dict, Any, Optional
import pyodbc

from app.core.config import settings
from app.core.tenant_context import get_current_client_id
from app.core.encryption import decrypt_credential
from app.core.connection_cache import connection_cache
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)

# ============================================
# CONSTANTES
# ============================================

DEFAULT_DATABASE_TYPE = "single"
SYSTEM_CLIENT_ID = settings.SUPERADMIN_CLIENTE_ID


# ============================================
# METADATA RESOLUTION
# ============================================

def _query_connection_metadata_from_db(client_id: int) -> Optional[Dict[str, Any]]:
    """
    Consulta DIRECTAMENTE la BD para obtener metadata de conexión.
    
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
    # Query para obtener metadata de conexión
    query = """
        SELECT 
            cmc.conexion_id,
            cmc.servidor,
            cmc.puerto,
            cmc.nombre_bd,
            cmc.usuario_encriptado,
            cmc.password_encriptado,
            cmc.tipo_bd,
            cmc.usa_ssl,
            c.tipo_instalacion,
            c.metadata_json
        FROM cliente_modulo_conexion cmc
        JOIN cliente c ON cmc.cliente_id = c.cliente_id
        WHERE 
            cmc.cliente_id = ? 
            AND cmc.es_activo = 1 
            AND cmc.es_conexion_principal = 1
        ORDER BY cmc.conexion_id DESC
    """
    
    conn = None
    cursor = None
    
    try:
        # CRÍTICO: Construir connection string ADMIN manualmente para evitar recursión
        admin_conn_str = (
            f"DRIVER={{{settings.DB_DRIVER}}};"
            f"SERVER={settings.DB_ADMIN_SERVER},{settings.DB_ADMIN_PORT};"
            f"DATABASE={settings.DB_ADMIN_DATABASE};"
            f"UID={settings.DB_ADMIN_USER};"
            f"PWD={settings.DB_ADMIN_PASSWORD};"
            "TrustServerCertificate=yes;"
        )
        
        conn = pyodbc.connect(admin_conn_str)
        cursor = conn.cursor()
        cursor.execute(query, (client_id,))
        
        row = cursor.fetchone()
        
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
        
        # Determinar database_type
        database_isolation = metadata_json.get("database_isolation", False)
        
        # Si tiene database_isolation=true en metadata → Multi-DB
        if database_isolation:
            database_type = "multi"
        else:
            database_type = "single"
        
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
        
    except pyodbc.Error as db_err:
        logger.error(
            f"[METADATA] Error de BD al consultar metadata para cliente {client_id}: {db_err}",
            exc_info=True
        )
        return None
        
    except Exception as e:
        logger.error(
            f"[METADATA] Error inesperado al consultar metadata para cliente {client_id}: {e}",
            exc_info=True
        )
        return None
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_connection_metadata(client_id: int) -> Dict[str, Any]:
    """
    Obtiene metadata de conexión para un cliente (con cache).
    
    FLUJO:
    1. Intentar obtener del cache
    2. Si no está en cache, consultar BD
    3. Guardar en cache
    4. Si falla o no existe → Fallback a Single-DB
    
    Args:
        client_id: ID del cliente
    
    Returns:
        Dict con metadata (siempre retorna algo, nunca None)
    
    Fallback garantizado:
        Si cualquier cosa falla, retorna metadata para Single-DB
    """
    # Caso especial: SYSTEM siempre usa Single-DB
    if client_id == SYSTEM_CLIENT_ID:
        logger.debug(f"[METADATA] Cliente {client_id} es SYSTEM, usando Single-DB")
        return {
            "database_type": "single",
            "nombre_bd": settings.DB_DATABASE,
            "tipo_instalacion": "cloud"
        }
    
    # Intentar obtener del cache
    cached_metadata = connection_cache.get(client_id)
    
    if cached_metadata:
        logger.debug(f"[METADATA] Cache HIT para cliente {client_id}")
        return cached_metadata
    
    # No está en cache, consultar BD
    logger.debug(f"[METADATA] Cache MISS para cliente {client_id}, consultando BD...")
    
    try:
        metadata = _query_connection_metadata_from_db(client_id)
        
        if metadata:
            # Guardar en cache
            connection_cache.set(client_id, metadata)
            logger.info(
                f"[METADATA] Metadata cargada para cliente {client_id}: "
                f"{metadata['database_type']} - {metadata['nombre_bd']}"
            )
            return metadata
        else:
            # No hay configuración → Fallback a Single-DB
            logger.warning(
                f"[METADATA] No se encontró configuración para cliente {client_id}, "
                f"usando Single-DB como fallback"
            )
            fallback_metadata = {
                "database_type": "single",
                "nombre_bd": settings.DB_DATABASE,
                "tipo_instalacion": "cloud"
            }
            # También cachear el fallback
            connection_cache.set(client_id, fallback_metadata)
            return fallback_metadata
            
    except Exception as e:
        logger.error(
            f"[METADATA] Error crítico al obtener metadata para cliente {client_id}: {e}",
            exc_info=True
        )
        # Fallback de emergencia
        return {
            "database_type": "single",
            "nombre_bd": settings.DB_DATABASE,
            "tipo_instalacion": "cloud"
        }


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


def get_client_db_connection_string(client_id: int) -> str:
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
        logger.warning(
            "[TENANT_CONN] Llamada fuera de contexto de request. "
            f"Usando SYSTEM_CLIENT_ID={SYSTEM_CLIENT_ID}"
        )
        client_id = SYSTEM_CLIENT_ID
    
    # Obtener connection string apropiado
    conn_str = get_client_db_connection_string(client_id)
    
    try:
        # Conectar
        conn = pyodbc.connect(conn_str, timeout=30)
        
        logger.debug(f"[TENANT_CONN] Conexión establecida para cliente {client_id}")
        
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


# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

def invalidate_client_connection_cache(client_id: int) -> bool:
    """
    Invalida el cache de metadata para un cliente específico.
    
    CUÁNDO USAR:
    - Después de actualizar cliente_modulo_conexion
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


def get_database_type(client_id: int) -> str:
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
# LOGGING DE INICIALIZACIÓN
# ============================================

logger.info(
    f"Módulo multi_db cargado. "
    f"SYSTEM_CLIENT_ID={SYSTEM_CLIENT_ID}, "
    f"DEFAULT_TYPE={DEFAULT_DATABASE_TYPE}"
)