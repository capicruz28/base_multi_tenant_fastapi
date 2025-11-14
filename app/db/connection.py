# app/db/connection.py (MODIFICADO)
import pyodbc
from app.core.config import settings
from contextlib import contextmanager
import logging
from app.core.exceptions import DatabaseError
from enum import Enum
from typing import Iterator

# CRÍTICO: Importar la nueva función que resuelve la conexión por cliente_id
from app.core.multi_db import get_db_connection_for_current_tenant 

logger = logging.getLogger(__name__)

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


@contextmanager
def get_db_connection(connection_type: DatabaseConnection = DatabaseConnection.DEFAULT) -> Iterator[pyodbc.Connection]:
    """
    Context manager para obtener y cerrar una conexión a BD.
    
    Si connection_type es DEFAULT, utiliza el contexto del tenant.
    Si connection_type es ADMIN, utiliza la conexión de administración fija.
    """
    conn = None
    try:
        if connection_type == DatabaseConnection.DEFAULT:
            # CRÍTICO: Usa la función tenant-aware
            conn = get_db_connection_for_current_tenant()
            logger.debug(f"Conexión a BD (DEFAULT/TENANT) establecida para Cliente ID: {conn.client_id if hasattr(conn, 'client_id') else 'N/A'}.")
        else:
            # Conexión ADMIN (mantenemos la lógica original)
            conn_str = get_connection_string(connection_type)
            conn = pyodbc.connect(conn_str)
            logger.debug(f"Conexión a BD ({connection_type.value}) establecida.")
            
        yield conn

    except pyodbc.Error as e:
        logger.error(f"Error de conexión a la base de datos ({connection_type.value}): {str(e)}", exc_info=True)
        # Aseguramos un mensaje de error consistente
        raise DatabaseError(status_code=500, detail=f"Error de conexión: {str(e)}")

    except Exception as e:
        logger.error(f"Error general en la gestión de conexión: {str(e)}", exc_info=True)
        raise

    finally:
        if conn:
            conn.close()
            logger.debug(f"Conexión a BD ({connection_type.value}) cerrada.")

# Asume que test_drivers está definido en alguna parte de tu código original, si no, añádelo:
# def test_drivers():
#     return pyodbc.drivers()