# app/infrastructure/database/queries_async.py
"""
Funciones de ejecución de queries ASYNC usando SQLAlchemy Core.

✅ FASE 2: Reemplazo completo de queries.py síncrono
- Todas las funciones son async
- Usa SQLAlchemy AsyncSession
- Acepta objetos SQLAlchemy Core (Select, Update, Delete, Insert)
- Aplica filtro de tenant automáticamente

USO:
    from app.infrastructure.database.queries_async import execute_query
    
    query = select(UsuarioTable).where(UsuarioTable.c.nombre_usuario == username)
    results = await execute_query(query)
"""

from typing import List, Dict, Any, Optional, Union, Tuple
from uuid import UUID
from sqlalchemy import Select, Update, Delete, Insert, text, TextClause
from sqlalchemy.sql import ClauseElement
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection_async import get_db_connection, DatabaseConnection
from app.core.tenant.routing import get_connection_for_tenant
from app.infrastructure.database.query_helpers import apply_tenant_filter, get_table_name_from_query
from app.core.exceptions import DatabaseError, ValidationError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def _get_connection_context(
    connection_type: DatabaseConnection,
    client_id: Optional[int] = None
):
    """
    ✅ FASE 5: Helper para obtener el contexto de conexión apropiado.
    
    Retorna el context manager correcto según el tipo de conexión:
    - ADMIN: get_db_connection(ADMIN)
    - DEFAULT: get_connection_for_tenant() (routing centralizado)
    """
    if connection_type == DatabaseConnection.ADMIN:
        return get_db_connection(connection_type)
    else:
        # Convertir client_id a UUID si es necesario
        from uuid import UUID
        cliente_id_uuid = None
        if client_id:
            if isinstance(client_id, UUID):
                cliente_id_uuid = client_id
            elif isinstance(client_id, int):
                try:
                    cliente_id_uuid = UUID(int=client_id) if client_id > 0 else None
                except (ValueError, OverflowError):
                    cliente_id_uuid = None
        
        return get_connection_for_tenant(cliente_id=cliente_id_uuid)


async def execute_query(
    query: Union[str, ClauseElement],
    params: Optional[Union[Tuple[Any, ...], Dict[str, Any]]] = None,
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[Union[int, UUID]] = None,
    skip_tenant_validation: bool = False
) -> List[Dict[str, Any]]:
    """
    Ejecuta una consulta SQL de forma async.
    
    ✅ FASE 2: Versión async que reemplaza execute_query síncrono.
    
    Args:
        query: Consulta SQL (string) o objeto SQLAlchemy Core (Select, Update, Delete, Insert)
        params: Parámetros opcionales (tupla o dict). Si es tupla y query tiene '?', se convierte a parámetros nombrados.
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente específico (opcional, puede ser int o UUID)
        skip_tenant_validation: Si True, omite la validación de tenant
    
    Returns:
        Lista de diccionarios con los resultados
    
    Raises:
        DatabaseError: Si hay error en la ejecución
    """
    # ✅ FASE 2: Si es objeto SQLAlchemy Core, aplicar filtro de tenant programáticamente
    if isinstance(query, (Select, Update, Delete, Insert)):
        # Obtener nombre de tabla para verificar si es global
        try:
            table_name = get_table_name_from_query(query)
        except Exception:
            table_name = None
        
        # Aplicar filtro de tenant automáticamente (si no se omite)
        if not skip_tenant_validation:
            query = apply_tenant_filter(query, client_id=client_id, table_name=table_name)
        
        # ✅ FASE 5: Usar routing centralizado
        async with _get_connection_context(connection_type, client_id) as session:
            try:
                result = await session.execute(query)
                
                # Si es SELECT, obtener resultados
                if isinstance(query, Select):
                    rows = result.fetchall()
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in rows]
                else:
                    # UPDATE/DELETE/INSERT: retornar información de filas afectadas
                    await session.commit()
                    return [{"rows_affected": result.rowcount}]
                    
            except Exception as e:
                await session.rollback()
                logger.error(f"Error en execute_query async: {str(e)}")
                raise DatabaseError(
                    detail=f"Error en la consulta: {str(e)}",
                    internal_code="DB_QUERY_ERROR"
                )
    
    elif isinstance(query, TextClause):
        # ✅ Aceptar TextClause (resultado de text().bindparams())
        # ✅ FASE 5: Usar routing centralizado
        async with _get_connection_context(connection_type, client_id) as session:
            try:
                result = await session.execute(query)
                rows = result.fetchall()
                columns = result.keys()
                return [dict(zip(columns, row)) for row in rows]
            except Exception as e:
                await session.rollback()
                logger.error(f"Error en execute_query async (TextClause): {str(e)}")
                raise DatabaseError(
                    detail=f"Error en la consulta: {str(e)}",
                    internal_code="DB_QUERY_ERROR"
                )
    
    elif isinstance(query, str):
        # ⚠️ DEPRECATED: Queries string (mantener compatibilidad temporal)
        logger.warning(
            "[QUERY] DEPRECATED: execute_query() recibió string SQL. "
            "Migrar a SQLAlchemy Core."
        )
        
        # String SQL - convertir ? a parámetros nombrados si hay params
        if params is not None:
            # Contar cuántos ? hay en la query
            question_marks = query.count('?')
            if question_marks > 0:
                # Convertir tupla o lista a dict con nombres param0, param1, etc.
                if isinstance(params, (tuple, list)):
                    if len(params) == 0:
                        logger.warning("execute_query recibió params vacío, ejecutando query sin parámetros")
                        query = text(query)
                    else:
                        param_names = [f"param{i}" for i in range(len(params))]
                        query_text = query
                        for i, name in enumerate(param_names):
                            query_text = query_text.replace("?", f":{name}", 1)
                        params_dict = dict(zip(param_names, params))
                        query = text(query_text).bindparams(**params_dict)
                elif isinstance(params, dict):
                    # Si ya es dict, convertir ? a :param_name
                    if len(params) == 0:
                        logger.warning("execute_query recibió params dict vacío, ejecutando query sin parámetros")
                        query = text(query)
                    else:
                        query_text = query
                        for key in params.keys():
                            query_text = query_text.replace("?", f":{key}", 1)
                        query = text(query_text).bindparams(**params)
                else:
                    logger.warning(f"execute_query recibió params de tipo inesperado: {type(params)}, ejecutando query sin parámetros")
                    query = text(query)
            else:
                query = text(query)
        else:
            query = text(query)
        
        # ✅ FASE 5: Usar routing centralizado
        async with _get_connection_context(connection_type, client_id) as session:
            try:
                result = await session.execute(query)
                rows = result.fetchall()
                columns = result.keys()
                return [dict(zip(columns, row)) for row in rows]
            except Exception as e:
                await session.rollback()
                logger.error(f"Error en execute_query async (string): {str(e)}")
                raise DatabaseError(
                    detail=f"Error en la consulta: {str(e)}",
                    internal_code="DB_QUERY_ERROR"
                )
    else:
        raise ValueError(
            f"query debe ser string SQL o objeto SQLAlchemy Core, recibido: {type(query)}"
        )


async def execute_auth_query(
    query: Union[str, Select, TextClause],
    params: Optional[Union[tuple, dict]] = None,
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT
) -> Optional[Dict[str, Any]]:
    """
    Ejecuta una consulta específica para autenticación y retorna un único registro.
    
    ✅ FASE 2: Versión async.
    
    Args:
        query: Consulta SQL (string), objeto SQLAlchemy Core (Select), o TextClause
        params: Parámetros opcionales (tupla o dict). Si es tupla y query tiene '?', se convierte a parámetros nombrados.
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
    
    Returns:
        Diccionario con el registro o None si no existe
    """
    if isinstance(query, Select):
        # ✅ FASE 5: Usar routing centralizado
        async with _get_connection_context(connection_type) as session:
            try:
                result = await session.execute(query)
                row = result.fetchone()
                
                if row:
                    columns = result.keys()
                    return dict(zip(columns, row))
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error en execute_auth_query async: {str(e)}")
                raise DatabaseError(
                    detail=f"Error en la autenticación: {str(e)}",
                    internal_code="DB_AUTH_ERROR"
                )
    
    elif isinstance(query, TextClause):
        # ✅ Aceptar TextClause (resultado de text().bindparams())
        async with _get_connection_context(connection_type) as session:
            try:
                result = await session.execute(query)
                row = result.fetchone()
                
                if row:
                    columns = result.keys()
                    return dict(zip(columns, row))
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error en execute_auth_query async (TextClause): {str(e)}")
                raise DatabaseError(
                    detail=f"Error en la autenticación: {str(e)}",
                    internal_code="DB_AUTH_ERROR"
                )
    
    elif isinstance(query, str):
        # String SQL - convertir ? a parámetros nombrados si hay params
        if params is not None:
            # Contar cuántos ? hay en la query
            question_marks = query.count('?')
            if question_marks > 0:
                # Convertir tupla o lista a dict con nombres param0, param1, etc.
                if isinstance(params, (tuple, list)):
                    if len(params) == 0:
                        logger.warning("execute_auth_query recibió params vacío, ejecutando query sin parámetros")
                        query = text(query)
                    else:
                        param_names = [f"param{i}" for i in range(len(params))]
                        query_text = query
                        for i, name in enumerate(param_names):
                            query_text = query_text.replace("?", f":{name}", 1)
                        params_dict = dict(zip(param_names, params))
                        logger.debug(f"execute_auth_query: convirtiendo ? a parámetros nombrados: {params_dict}")
                        query = text(query_text).bindparams(**params_dict)
                elif isinstance(params, dict):
                    # Si ya es dict, convertir ? a :param_name
                    if len(params) == 0:
                        logger.warning("execute_auth_query recibió params dict vacío, ejecutando query sin parámetros")
                        query = text(query)
                    else:
                        query_text = query
                        for key in params.keys():
                            query_text = query_text.replace("?", f":{key}", 1)
                        query = text(query_text).bindparams(**params)
                else:
                    logger.warning(f"execute_auth_query recibió params de tipo inesperado: {type(params)}, ejecutando query sin parámetros")
                    query = text(query)
            else:
                query = text(query)
        else:
            query = text(query)
        
        async with _get_connection_context(connection_type) as session:
            try:
                result = await session.execute(query)
                row = result.fetchone()
                
                if row:
                    columns = result.keys()
                    return dict(zip(columns, row))
                return None
            except Exception as e:
                await session.rollback()
                logger.error(f"Error en execute_auth_query async (string): {str(e)}")
                raise DatabaseError(
                    detail=f"Error en la autenticación: {str(e)}",
                    internal_code="DB_AUTH_ERROR"
                )
    else:
        raise ValueError(
            f"query debe ser string SQL, objeto SQLAlchemy Core (Select), o TextClause, recibido: {type(query)}"
        )


async def execute_insert(
    query: Union[str, Insert, TextClause],
    params: Optional[Union[tuple, dict]] = None,
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[Union[int, UUID]] = None
) -> Dict[str, Any]:
    """
    Ejecuta una sentencia INSERT y retorna los datos insertados.
    
    ✅ FASE 2: Versión async.
    
    Args:
        query: Consulta SQL (string), objeto SQLAlchemy Core (Insert), o TextClause
        params: Parámetros opcionales (tupla o dict). Si es tupla y query tiene '?', se convierte a parámetros nombrados.
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente específico (opcional, puede ser int o UUID)
    
    Returns:
        Diccionario con los datos insertados (OUTPUT) y rows_affected
    """
    if isinstance(query, Insert):
        async with _get_connection_context(connection_type, client_id) as session:
            try:
                result = await session.execute(query)
                await session.commit()
                
                # Obtener datos insertados si hay OUTPUT
                if result.returns_rows:
                    row = result.fetchone()
                    if row:
                        columns = result.keys()
                        data = dict(zip(columns, row))
                        data["rows_affected"] = result.rowcount
                        return data
                
                return {"rows_affected": result.rowcount}
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error en execute_insert async: {str(e)}")
                raise DatabaseError(
                    detail=f"Error en la inserción: {str(e)}",
                    internal_code="DB_INSERT_ERROR"
                )
    
    elif isinstance(query, TextClause):
        # ✅ Aceptar TextClause (resultado de text().bindparams())
        async with _get_connection_context(connection_type, client_id) as session:
            try:
                result = await session.execute(query)
                await session.commit()
                
                if result.returns_rows:
                    row = result.fetchone()
                    if row:
                        columns = result.keys()
                        data = dict(zip(columns, row))
                        data["rows_affected"] = result.rowcount
                        return data
                
                return {"rows_affected": result.rowcount}
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error en execute_insert async (TextClause): {str(e)}")
                raise DatabaseError(
                    detail=f"Error en la inserción: {str(e)}",
                    internal_code="DB_INSERT_ERROR"
                )
    
    elif isinstance(query, str):
        # String SQL - convertir ? a parámetros nombrados si hay params
        if params is not None:
            # Contar cuántos ? hay en la query
            question_marks = query.count('?')
            if question_marks > 0:
                # Convertir tupla a dict con nombres param0, param1, etc.
                if isinstance(params, tuple):
                    param_names = [f"param{i}" for i in range(len(params))]
                    query_text = query
                    for i, name in enumerate(param_names):
                        query_text = query_text.replace("?", f":{name}", 1)
                    params_dict = dict(zip(param_names, params))
                    query = text(query_text).bindparams(**params_dict)
                elif isinstance(params, dict):
                    # Si ya es dict, convertir ? a :param_name
                    query_text = query
                    for key in params.keys():
                        query_text = query_text.replace("?", f":{key}", 1)
                    query = text(query_text).bindparams(**params)
                else:
                    query = text(query)
            else:
                query = text(query)
        else:
            query = text(query)
        
        async with _get_connection_context(connection_type, client_id) as session:
            try:
                result = await session.execute(query)
                await session.commit()
                
                if result.returns_rows:
                    row = result.fetchone()
                    if row:
                        columns = result.keys()
                        data = dict(zip(columns, row))
                        data["rows_affected"] = result.rowcount
                        return data
                
                return {"rows_affected": result.rowcount}
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error en execute_insert async (string): {str(e)}")
                raise DatabaseError(
                    detail=f"Error en la inserción: {str(e)}",
                    internal_code="DB_INSERT_ERROR"
                )
    else:
        raise ValueError(
            f"query debe ser string SQL, objeto SQLAlchemy Core (Insert), o TextClause, recibido: {type(query)}"
        )


async def execute_update(
    query: Union[str, Update, TextClause],
    params: Optional[Union[tuple, dict]] = None,
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[Union[int, UUID]] = None
) -> Dict[str, Any]:
    """
    Ejecuta una sentencia UPDATE y retorna los datos actualizados.
    
    ✅ FASE 2: Versión async.
    
    Args:
        query: Consulta SQL (string), objeto SQLAlchemy Core (Update), o TextClause
        params: Parámetros opcionales (tupla o dict). Si es tupla y query tiene '?', se convierte a parámetros nombrados.
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente específico (opcional, puede ser int o UUID)
    
    Returns:
        Diccionario con los datos actualizados (OUTPUT) y rows_affected
    """
    if isinstance(query, Update):
        async with _get_connection_context(connection_type, client_id) as session:
            try:
                result = await session.execute(query)
                await session.commit()
                
                if result.returns_rows:
                    row = result.fetchone()
                    if row:
                        columns = result.keys()
                        data = dict(zip(columns, row))
                        data["rows_affected"] = result.rowcount
                        return data
                
                return {"rows_affected": result.rowcount}
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error en execute_update async: {str(e)}")
                raise DatabaseError(
                    detail=f"Error en la actualización: {str(e)}",
                    internal_code="DB_UPDATE_ERROR"
                )
    
    elif isinstance(query, TextClause):
        # ✅ Aceptar TextClause (resultado de text().bindparams())
        async with _get_connection_context(connection_type, client_id) as session:
            try:
                result = await session.execute(query)
                await session.commit()
                
                if result.returns_rows:
                    row = result.fetchone()
                    if row:
                        columns = result.keys()
                        data = dict(zip(columns, row))
                        data["rows_affected"] = result.rowcount
                        return data
                
                return {"rows_affected": result.rowcount}
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error en execute_update async (TextClause): {str(e)}")
                raise DatabaseError(
                    detail=f"Error en la actualización: {str(e)}",
                    internal_code="DB_UPDATE_ERROR"
                )
    
    elif isinstance(query, str):
        # String SQL - convertir ? a parámetros nombrados si hay params
        if params is not None:
            # Contar cuántos ? hay en la query
            question_marks = query.count('?')
            if question_marks > 0:
                # Convertir tupla a dict con nombres param0, param1, etc.
                if isinstance(params, tuple):
                    param_names = [f"param{i}" for i in range(len(params))]
                    query_text = query
                    for i, name in enumerate(param_names):
                        query_text = query_text.replace("?", f":{name}", 1)
                    params_dict = dict(zip(param_names, params))
                    query = text(query_text).bindparams(**params_dict)
                elif isinstance(params, dict):
                    # Si ya es dict, convertir ? a :param_name
                    query_text = query
                    for key in params.keys():
                        query_text = query_text.replace("?", f":{key}", 1)
                    query = text(query_text).bindparams(**params)
                else:
                    query = text(query)
            else:
                query = text(query)
        else:
            query = text(query)
        
        async with _get_connection_context(connection_type, client_id) as session:
            try:
                result = await session.execute(query)
                await session.commit()
                
                if result.returns_rows:
                    row = result.fetchone()
                    if row:
                        columns = result.keys()
                        data = dict(zip(columns, row))
                        data["rows_affected"] = result.rowcount
                        return data
                
                return {"rows_affected": result.rowcount}
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error en execute_update async (string): {str(e)}")
                raise DatabaseError(
                    detail=f"Error en la actualización: {str(e)}",
                    internal_code="DB_UPDATE_ERROR"
                )
    else:
        raise ValueError(
            f"query debe ser string SQL, objeto SQLAlchemy Core (Update), o TextClause, recibido: {type(query)}"
        )


async def execute_procedure(
    procedure_name: str,
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Ejecuta un stored procedure sin parámetros de forma async.
    
    ✅ FASE 2: Versión async.
    
    Args:
        procedure_name: Nombre del stored procedure
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente específico (opcional)
    
    Returns:
        Lista de diccionarios con los resultados
    """
    async with _get_connection_context(connection_type, client_id) as session:
        try:
            # Ejecutar stored procedure usando text() con formato SQL Server
            query = text(f"EXEC {procedure_name}")
            result = await session.execute(query)
            rows = result.fetchall()
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            await session.rollback()
            logger.error(f"Error en execute_procedure async: {str(e)}")
            raise DatabaseError(
                detail=f"Error ejecutando stored procedure {procedure_name}: {str(e)}",
                internal_code="DB_PROCEDURE_ERROR"
            )


async def execute_procedure_params(
    procedure_name: str,
    params_dict: Dict[str, Any],
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Ejecuta un stored procedure con parámetros nombrados de forma async.
    
    ✅ FASE 2: Versión async.
    
    Args:
        procedure_name: Nombre del stored procedure
        params_dict: Diccionario con parámetros nombrados (ej: {'UsuarioID': 123})
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente específico (opcional)
    
    Returns:
        Lista de diccionarios con los resultados
    """
    async with _get_connection_context(connection_type, client_id) as session:
        try:
            # Construir lista de parámetros para SQL Server
            # Formato: @ParamName = :param_name (SQLAlchemy usa :param_name para bindings)
            param_list = []
            param_bindings = {}
            for key, value in params_dict.items():
                param_name = f"@{key}"
                # ✅ Convertir UUID a string para stored procedures
                # SQL Server puede convertir strings a UNIQUEIDENTIFIER automáticamente
                # cuando el stored procedure espera UNIQUEIDENTIFIER como tipo de parámetro
                if isinstance(value, UUID):
                    # Pasar como string - SQL Server lo convertirá automáticamente si el SP espera UNIQUEIDENTIFIER
                    param_bindings[key] = str(value)
                    param_list.append(f"{param_name} = :{key}")
                else:
                    param_bindings[key] = value
                    param_list.append(f"{param_name} = :{key}")
            
            # Construir query con parámetros
            params_str = ", ".join(param_list) if param_list else ""
            query_str = f"EXEC {procedure_name} {params_str}".strip()
            query = text(query_str)
            
            result = await session.execute(query, param_bindings)
            
            # Manejar múltiples result sets si existen
            results = []
            while True:
                if result.returns_rows:
                    rows = result.fetchall()
                    if rows:
                        columns = result.keys()
                        results.extend([dict(zip(columns, row)) for row in rows])
                
                # Intentar obtener el siguiente result set
                try:
                    # En SQLAlchemy async, necesitamos usar nextset() si está disponible
                    # Por ahora, solo procesamos el primer result set
                    break
                except Exception:
                    break
            
            return results if results else []
        except Exception as e:
            await session.rollback()
            logger.error(f"Error en execute_procedure_params async: {str(e)}")
            raise DatabaseError(
                detail=f"Error ejecutando stored procedure {procedure_name}: {str(e)}",
                internal_code="DB_PROCEDURE_ERROR"
            )
