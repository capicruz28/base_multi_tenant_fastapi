# app/core/multi_db.py
"""
Gestión de múltiples conexiones de base de datos para el soporte multi-tenant.
En la implementación actual, se mantiene una sola conexión, pero se encapsula 
la lógica para permitir la futura expansión a bases de datos dedicadas por cliente.
"""

import logging
from typing import Dict, Any, Optional
import pyodbc
from app.core.config import settings
from app.core.tenant_context import get_current_client_id

logger = logging.getLogger(__name__)

# Cache para almacenar objetos de conexión o connection strings específicos por cliente
# Key: cliente_id (int), Value: connection string o dict de config
DB_CONNECTION_CACHE: Dict[int, Any] = {}

def get_client_db_connection_string(client_id: int) -> str:
    """
    Determina y retorna la cadena de conexión de la BD para un cliente específico.
    
    Por ahora, todos los clientes usan la BD Centralizada (bd_sistema), pero
    esta función es el punto de extensión para BDs dedicadas.
    """
    
    # Lógica Centralizada (FASE 1 - Modelo Inicial)
    if client_id == settings.SUPERADMIN_CLIENTE_ID:
        # El cliente SYSTEM usa las credenciales principales del sistema
        pass
    
    # En un futuro, aquí se consultaría la tabla 'cliente_config'
    # para obtener una cadena de conexión o credenciales dedicadas.
    
    # Crear la cadena de conexión base (compatible con app/db/connection.py)
    conn_str = (
        f"DRIVER={{{settings.DB_DRIVER}}};"
        f"SERVER={settings.DB_SERVER};"
        f"DATABASE={settings.DB_DATABASE};"
        f"UID={settings.DB_USER};"
        f"PWD={settings.DB_PASSWORD};"
        "TDS_Version=7.4" # Asegura compatibilidad con versiones modernas
    )
    
    return conn_str

def get_db_connection_for_current_tenant() -> pyodbc.Connection:
    """
    Obtiene la conexión pyodbc para el cliente actual en el contexto.
    """
    try:
        # Intentar obtener el ID del contexto. Esto fallará si se llama sin middleware.
        client_id = get_current_client_id()
    except RuntimeError:
        # Si falla (ej: inicialización, scripts de fondo), usa el ID del SYSTEM.
        logger.warning("Llamada a get_db_connection_for_current_tenant fuera de un contexto de request. Usando ID de SYSTEM.")
        client_id = settings.SUPERADMIN_CLIENTE_ID

    conn_str = get_client_db_connection_string(client_id)
    
    try:
        # Se podría implementar un pool de conexiones por cliente en la cache,
        # pero por ahora, solo generamos la conexión.
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as e:
        logger.critical(f"Error CRÍTICO de conexión a BD para Cliente ID {client_id}: {e}")
        # Envolviendo el error pyodbc en un error de la aplicación si es necesario
        raise ConnectionError(f"Fallo al conectar a la BD del cliente {client_id}.")