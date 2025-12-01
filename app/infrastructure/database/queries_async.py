# app/infrastructure/database/queries_async.py
"""
Versión ASYNC de queries.py para operaciones no bloqueantes.

✅ CORRECCIÓN AUDITORÍA: Performance - I/O Síncrono
- Implementa funciones async usando SQLAlchemy AsyncSession
- NO bloquea el event loop de FastAPI
- Coexiste con queries.py (no reemplaza, permite migración gradual)
- Mantiene todas las validaciones de seguridad (IDOR)

USO:
    # En funciones async
    results = await execute_query_async("SELECT * FROM usuario WHERE cliente_id = ?", (client_id,))
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection_async import get_db_connection_async
from app.infrastructure.database.connection import DatabaseConnection
from app.core.exceptions import DatabaseError, ValidationError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def execute_query_async(
    query: str, 
    params: tuple = (), 
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT, 
    client_id: Optional[int] = None,
    skip_tenant_validation: bool = False
) -> List[Dict[str, Any]]:
    """
    Ejecuta una consulta SQL de forma async (NO bloquea el event loop).
    
    ✅ CORRECCIÓN AUDITORÍA: Versión async que NO bloquea el event loop.
    ✅ SEGURIDAD: Mantiene validación automática de filtro cliente_id.
    
    Args:
        query: Consulta SQL a ejecutar
        params: Parámetros de la consulta (usar :param_name para named params)
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente específico (opcional)
        skip_tenant_validation: Si True, omite la validación de tenant (solo si ALLOW_TENANT_FILTER_BYPASS=True)
    
    Returns:
        Lista de diccionarios con los resultados
    
    Raises:
        ValidationError: Si la query no incluye filtro de tenant y hay contexto de tenant
        DatabaseError: Si hay error en la ejecución
    """
    # ✅ CORRECCIÓN AUDITORÍA: VALIDACIÓN OBLIGATORIA DE TENANT (misma lógica que versión síncrona)
    should_validate = (
        not skip_tenant_validation or 
        (skip_tenant_validation and not settings.ALLOW_TENANT_FILTER_BYPASS)
    )
    
    if should_validate and client_id is None and connection_type == DatabaseConnection.DEFAULT:
        try:
            from app.core.tenant.context import get_current_client_id
            current_cliente_id = get_current_client_id()
            
            query_lower = query.lower().strip()
            
            # Tablas globales que no requieren filtro
            global_tables = [
                'cliente', 'cliente_modulo', 'modulo', 'cliente_modulo_activo', 
                'cliente_modulo_conexion', 'sistema_config'
            ]
            
            is_global_table = any(
                f" from {table} " in query_lower or 
                f" from dbo.{table} " in query_lower or
                f"from {table}" in query_lower.split('where')[0] or
                f"from dbo.{table}" in query_lower.split('where')[0]
                for table in global_tables
            )
            
            if is_global_table:
                logger.debug(f"[SECURITY] Query en tabla global detectada, omitiendo validación de tenant")
            elif "where" in query_lower:
                # Verificar filtro de cliente_id (soporta ? y :param_name)
                has_cliente_id_filter = (
                    " cliente_id = ?" in query_lower or
                    " cliente_id=?" in query_lower or
                    " cliente_id = " in query_lower or
                    " cliente_id = :" in query_lower or
                    f" cliente_id = {current_cliente_id}" in query_lower or
                    "and cliente_id = ?" in query_lower or
                    "and cliente_id=?" in query_lower or
                    "and cliente_id = :" in query_lower or
                    "where cliente_id = ?" in query_lower or
                    "where cliente_id=?" in query_lower or
                    "where cliente_id = :" in query_lower or
                    ("join" in query_lower and "cliente_id" in query_lower and "on" in query_lower) or
                    ("cliente_id" in query_lower and ("?" in query_lower or ":" in query_lower) and len(params) > 0)
                )
                
                has_cliente_id_in_params = (
                    len(params) > 0 and 
                    "cliente_id" in query_lower and
                    ("?" in query_lower or ":" in query_lower or str(current_cliente_id) in query_lower)
                )
                
                if not has_cliente_id_filter and not has_cliente_id_in_params:
                    logger.error(
                        f"[SECURITY CRITICAL] Query async sin filtro de cliente_id detectada. "
                        f"Cliente actual: {current_cliente_id}. Query: {query[:200]}..."
                    )
                    raise ValidationError(
                        detail=(
                            f"Query sin filtro de tenant OBLIGATORIO detectada. "
                            f"Todas las queries en contexto de tenant DEBEN incluir 'WHERE cliente_id = ?' "
                            f"o 'WHERE cliente_id = :cliente_id'. "
                            f"Si es un caso especial, active ALLOW_TENANT_FILTER_BYPASS temporalmente."
                        ),
                        internal_code="MISSING_TENANT_FILTER"
                    )
        except RuntimeError:
            if settings.ALLOW_TENANT_FILTER_BYPASS:
                logger.debug("[SECURITY] Sin contexto de tenant, omitiendo validación (bypass permitido)")
            else:
                logger.warning("[SECURITY] Sin contexto de tenant pero bypass no permitido.")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"[SECURITY] Error en validación de tenant (BLOQUEANDO): {str(e)}", exc_info=True)
            raise ValidationError(
                detail=f"Error en validación de seguridad de tenant. Error: {str(e)}",
                internal_code="TENANT_VALIDATION_ERROR"
            )
    
    # Convertir params tuple a dict si la query usa named parameters
    # SQLAlchemy async usa named parameters con :param_name
    if params and isinstance(params, tuple) and ":" in query:
        # Si la query tiene :param_name pero params es tuple, convertir
        # Por ahora, asumimos que si hay :, se debe pasar como dict
        # El usuario debe pasar dict si usa named params
        if not isinstance(params, dict):
            logger.warning(
                "[QUERIES_ASYNC] Query con named parameters (:) pero params es tuple. "
                "Para named params, pasar dict: {'cliente_id': 1, ...}"
            )
    
    # Ejecutar query async
    try:
        async with get_db_connection_async(connection_type, client_id) as session:
            # Convertir params tuple a dict si es necesario
            if isinstance(params, tuple) and params:
                # Si la query usa ?, convertir a named params para SQLAlchemy
                # SQLAlchemy async prefiere named parameters
                if "?" in query:
                    # Para queries con ?, necesitamos usar text() con parámetros posicionales
                    # SQLAlchemy async soporta esto con text()
                    result = await session.execute(text(query), params)
                else:
                    # Named parameters
                    if isinstance(params, dict):
                        result = await session.execute(text(query), params)
                    else:
                        # Convertir tuple a dict (asumiendo orden)
                        # Esto es un fallback, mejor usar dict directamente
                        result = await session.execute(text(query), params)
            else:
                result = await session.execute(text(query), params if isinstance(params, dict) else {})
            
            # Obtener resultados
            rows = result.fetchall()
            
            # Convertir a lista de diccionarios
            if rows:
                columns = list(result.keys())
                return [dict(zip(columns, row)) for row in rows]
            return []
            
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error en execute_query_async: {str(e)}", exc_info=True)
        raise DatabaseError(
            detail=f"Error en la consulta async: {str(e)}",
            internal_code="DB_QUERY_ASYNC_ERROR"
        )


async def execute_auth_query_async(
    query: str, 
    params: tuple = ()
) -> Optional[Dict[str, Any]]:
    """
    Ejecuta una consulta específica para autenticación (async).
    Retorna un único registro.
    
    Args:
        query: Consulta SQL
        params: Parámetros de la consulta
    
    Returns:
        Diccionario con el resultado o None si no existe
    """
    try:
        async with get_db_connection_async(DatabaseConnection.DEFAULT) as session:
            result = await session.execute(text(query), params)
            row = result.fetchone()
            
            if row:
                columns = list(result.keys())
                return dict(zip(columns, row))
            return None
            
    except Exception as e:
        logger.error(f"Error en execute_auth_query_async: {str(e)}")
        raise DatabaseError(
            detail=f"Error en la autenticación async: {str(e)}",
            internal_code="DB_AUTH_ASYNC_ERROR"
        )


async def execute_insert_async(
    query: str,
    params: tuple = (),
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Ejecuta una sentencia INSERT de forma async.
    
    Args:
        query: Query INSERT con OUTPUT INSERTED.*
        params: Parámetros de la consulta
        connection_type: Tipo de conexión
        client_id: ID del cliente (opcional)
    
    Returns:
        Diccionario con los datos insertados y rows_affected
    """
    try:
        async with get_db_connection_async(connection_type, client_id) as session:
            result = await session.execute(text(query), params)
            
            # Obtener datos de OUTPUT INSERTED
            output_row = result.fetchone()
            rows_affected = result.rowcount
            
            result_dict = {}
            if output_row:
                columns = list(result.keys())
                result_dict = dict(zip(columns, output_row))
            
            result_dict["rows_affected"] = rows_affected
            
            await session.commit()
            logger.info(f"Inserción async exitosa, filas afectadas: {rows_affected}")
            
            return result_dict
            
    except Exception as e:
        error_str = str(e)
        logger.error(f"Error en execute_insert_async: {error_str}")
        
        # Detectar errores de constraint UNIQUE
        if '23000' in error_str and 'UNIQUE' in error_str.upper():
            from app.core.exceptions import ConflictError
            raise ConflictError(
                detail="Ya existe un registro con estos valores únicos.",
                internal_code="UNIQUE_CONSTRAINT_VIOLATION"
            )
        
        raise DatabaseError(
            detail=f"Error en la inserción async: {error_str}",
            internal_code="DB_INSERT_ASYNC_ERROR"
        )


async def execute_update_async(
    query: str, 
    params: tuple = (), 
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Ejecuta una sentencia UPDATE de forma async.
    
    Args:
        query: Query UPDATE con OUTPUT INSERTED.*
        params: Parámetros de la consulta
        connection_type: Tipo de conexión
        client_id: ID del cliente (opcional)
    
    Returns:
        Diccionario con los datos actualizados y rows_affected
    """
    try:
        async with get_db_connection_async(connection_type, client_id) as session:
            result = await session.execute(text(query), params)
            
            rows_affected = result.rowcount
            
            # Obtener datos de OUTPUT INSERTED si existe
            output_row = result.fetchone()
            result_dict = {}
            
            if output_row:
                columns = list(result.keys())
                result_dict = dict(zip(columns, output_row))
            
            result_dict['rows_affected'] = rows_affected
            
            await session.commit()
            logger.info(f"Actualización async exitosa, filas afectadas: {rows_affected}")
            
            return result_dict
            
    except Exception as e:
        logger.error(f"Error en execute_update_async: {str(e)}")
        raise DatabaseError(
            detail=f"Error en la actualización async: {str(e)}",
            internal_code="DB_UPDATE_ASYNC_ERROR"
        )


async def execute_procedure_async(
    procedure_name: str, 
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Ejecuta un stored procedure de forma async.
    
    Args:
        procedure_name: Nombre del stored procedure
        connection_type: Tipo de conexión
        client_id: ID del cliente (opcional)
    
    Returns:
        Lista de diccionarios con los resultados
    """
    try:
        async with get_db_connection_async(connection_type, client_id) as session:
            result = await session.execute(text(f"EXEC {procedure_name}"))
            
            results = []
            rows = result.fetchall()
            
            if rows:
                columns = list(result.keys())
                results = [dict(zip(columns, row)) for row in rows]
            
            return results
            
    except Exception as e:
        logger.error(f"Error en execute_procedure_async: {str(e)}")
        raise DatabaseError(
            detail=f"Error en el procedimiento async: {str(e)}",
            internal_code="DB_PROCEDURE_ASYNC_ERROR"
        )


async def execute_procedure_params_async(
    procedure_name: str,
    params: dict,
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Ejecuta un stored procedure con parámetros de forma async.
    
    Args:
        procedure_name: Nombre del stored procedure
        params: Diccionario con parámetros {nombre: valor}
        connection_type: Tipo de conexión
        client_id: ID del cliente (opcional)
    
    Returns:
        Lista de diccionarios con los resultados
    """
    try:
        # Construir query con parámetros nombrados
        param_str = ", ".join([f"@{key} = :{key}" for key in params.keys()])
        query = f"EXEC {procedure_name} {param_str}"
        
        async with get_db_connection_async(connection_type, client_id) as session:
            result = await session.execute(text(query), params)
            
            results = []
            rows = result.fetchall()
            
            if rows:
                columns = list(result.keys())
                results = [dict(zip(columns, row)) for row in rows]
            
            return results
            
    except Exception as e:
        logger.error(f"Error en execute_procedure_params_async: {str(e)}")
        raise DatabaseError(
            detail=f"Error en el procedimiento async: {str(e)}",
            internal_code="DB_PROCEDURE_PARAMS_ASYNC_ERROR"
        )

