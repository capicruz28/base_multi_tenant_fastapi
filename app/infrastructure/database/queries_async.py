# app/infrastructure/database/queries_async.py
"""
Funciones de ejecución de queries ASYNC usando SQLAlchemy Core.

✅ FASE 2: Reemplazo completo de queries.py síncrono
- Todas las funciones son async
- Usa SQLAlchemy AsyncSession
- Acepta objetos SQLAlchemy Core (Select, Update, Delete, Insert)
- Aplica filtro de tenant automáticamente

Pipeline interno L6 (RD-06 / F1-WP06):
  1. Validar bypass tenant (si aplica)
  2. Resolver client_id (param > ContextVar)
  3. Clasificar operation_class (DEFAULT→tenant_data, ADMIN→control_plane)
  4. QueryAuditor + apply_tenant_filter (tenant_data, no global)
  5. _get_connection_context → resolución gateway → AsyncSession
  6. execute / commit / rollback

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
from app.core.tenant.routing import (
    get_connection_for_tenant,
    OPERATION_CLASS_CONTROL_PLANE,
    OPERATION_CLASS_TENANT_DATA,
)
from app.core.identity.identity_scope import IdentityScope
from app.core.identity.identity_store_connection import OPERATION_CLASS_TENANT_IDENTITY
from app.core.tenant.context import try_get_current_client_id
from app.infrastructure.database.query_helpers import (
    apply_tenant_filter,
    get_table_name_from_query,
    apply_tenant_filter_to_text_clause,
)
from app.core.exceptions import DatabaseError, ValidationError, SecurityError
from app.core.config import settings
from app.core.security.query_auditor import QueryAuditor
import logging

logger = logging.getLogger(__name__)


def _operation_class_for(connection_type: DatabaseConnection) -> str:
    """RD-07: DEFAULT→tenant_data, ADMIN→control_plane."""
    if connection_type == DatabaseConnection.ADMIN:
        return OPERATION_CLASS_CONTROL_PLANE
    return OPERATION_CLASS_TENANT_DATA


def _normalize_operation_class(operation_class: Optional[str]) -> str:
    """Identity store alias → tenant_data para routing/cache L-A."""
    if operation_class == OPERATION_CLASS_TENANT_IDENTITY:
        return OPERATION_CLASS_TENANT_DATA
    if operation_class:
        return operation_class
    return OPERATION_CLASS_TENANT_DATA


def _coerce_client_id_uuid(
    client_id: Optional[Union[int, UUID]],
) -> Optional[UUID]:
    if client_id is None:
        return None
    if isinstance(client_id, UUID):
        return client_id
    if isinstance(client_id, int):
        try:
            return UUID(int=client_id) if client_id > 0 else None
        except (ValueError, OverflowError):
            return None
    return None


def _resolve_effective_client_id(
    client_id: Optional[Union[int, UUID]],
) -> Optional[UUID]:
    """Paso 2 gateway: param explícito > ContextVar."""
    coerced = _coerce_client_id_uuid(client_id)
    if coerced is not None:
        return coerced
    return try_get_current_client_id()


def _assert_skip_tenant_validation_allowed(skip_tenant_validation: bool) -> None:
    if not skip_tenant_validation:
        return
    if not settings.ALLOW_TENANT_FILTER_BYPASS:
        raise ValidationError(
            detail=(
                "Bypass de validación de tenant no permitido. "
                "Para usar skip_tenant_validation=True, debe activar ALLOW_TENANT_FILTER_BYPASS en configuración. "
                "⚠️ ADVERTENCIA: Esto solo debe usarse en scripts de migración o mantenimiento."
            ),
            internal_code="TENANT_VALIDATION_BYPASS_DISABLED",
        )
    logger.warning(
        "[SECURITY WARNING] Bypass de validación de tenant permitido para query. "
        "Esto solo debería usarse en scripts de migración o mantenimiento."
    )


def _infer_table_name_from_sql_text(query_str: str) -> Optional[str]:
    query_lower = query_str.lower()
    for keyword in ("from", "update", "delete from", "insert into"):
        if keyword in query_lower:
            parts = query_lower.split(keyword, 1)
            if len(parts) > 1:
                table_part = parts[1].strip().split()[0].strip(";").strip("(")
                return table_part
    return None


def _run_query_auditor_if_enabled(
    query: Union[str, ClauseElement, TextClause],
    *,
    table_name: Optional[str],
    client_id: Optional[Union[int, UUID]],
    skip_tenant_validation: bool,
    context_label: str = "query",
) -> None:
    if skip_tenant_validation or not settings.ENABLE_QUERY_TENANT_VALIDATION:
        return
    try:
        QueryAuditor.validate_tenant_filter(
            query=query,
            table_name=table_name,
            client_id=client_id,
            skip_validation=False,
        )
    except Exception as audit_error:
        logger.warning(
            f"[QUERY_AUDITOR] Error en auditoría {context_label} (no bloqueante): {audit_error}"
        )
        if settings.ENVIRONMENT == "production":
            raise


def _prepare_core_query_for_gateway(
    query: ClauseElement,
    *,
    client_id: Optional[Union[int, UUID]],
    skip_tenant_validation: bool,
    identity_scope: Optional[IdentityScope] = None,
) -> ClauseElement:
    try:
        table_name = get_table_name_from_query(query)
    except Exception:
        table_name = None
    _run_query_auditor_if_enabled(
        query,
        table_name=table_name,
        client_id=client_id,
        skip_tenant_validation=skip_tenant_validation,
        context_label="Core",
    )
    if skip_tenant_validation:
        return query
    return apply_tenant_filter(
        query,
        client_id=client_id,
        table_name=table_name,
        identity_scope=identity_scope,
    )


def _prepare_text_clause_for_gateway(
    query: TextClause,
    *,
    client_id: Optional[Union[int, UUID]],
    table_name: Optional[str],
    skip_tenant_validation: bool,
    identity_scope: Optional[IdentityScope] = None,
) -> TextClause:
    effective_client_id = _resolve_effective_client_id(client_id)
    if table_name is None:
        try:
            query_str = query.text if hasattr(query, "text") else str(query)
        except Exception:
            query_str = str(query)
        table_name = _infer_table_name_from_sql_text(query_str)
    _run_query_auditor_if_enabled(
        query,
        table_name=table_name,
        client_id=effective_client_id,
        skip_tenant_validation=skip_tenant_validation,
        context_label="TextClause",
    )
    if skip_tenant_validation or not effective_client_id:
        return query
    return apply_tenant_filter_to_text_clause(
        query,
        client_id=effective_client_id,
        table_name=table_name,
        identity_scope=identity_scope,
    )


def _get_connection_context(
    connection_type: DatabaseConnection,
    client_id: Optional[Union[int, UUID]] = None,
    operation_class: Optional[str] = None,
):
    """
    Gateway L6 — apertura unificada de sesión (RD-06 / F1-WP06).

    Resolución → execute:
    - ADMIN / control_plane → get_db_connection(ADMIN)
    - DEFAULT / tenant_data → get_connection_for_tenant(operation_class, client_id)
    """
    operation_class = _normalize_operation_class(
        operation_class or _operation_class_for(connection_type)
    )
    if connection_type == DatabaseConnection.ADMIN:
        logger.debug("[GATEWAY] session op=%s store=control_plane", operation_class)
        return get_db_connection(DatabaseConnection.ADMIN)

    cliente_id_uuid = _coerce_client_id_uuid(client_id)
    logger.debug(
        "[GATEWAY] session op=%s store=tenant_data client=%s",
        operation_class,
        cliente_id_uuid,
    )
    return get_connection_for_tenant(
        cliente_id=cliente_id_uuid,
        operation_class=operation_class,
    )


async def execute_query(
    query: Union[str, ClauseElement],
    params: Optional[Union[Tuple[Any, ...], Dict[str, Any]]] = None,
    connection_type: DatabaseConnection = DatabaseConnection.DEFAULT,
    client_id: Optional[Union[int, UUID]] = None,
    skip_tenant_validation: bool = False,
    identity_scope: Optional[IdentityScope] = None,
    operation_class: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Ejecuta una consulta SQL de forma async con validación automática de tenant.
    
    ✅ FASE 2: Versión async que reemplaza execute_query síncrono.
    ✅ FASE 1 SEGURIDAD: Validación de tenant obligatoria por defecto.
    
    Esta función es el punto central de acceso a la base de datos. Aplica automáticamente
    filtros de tenant para garantizar aislamiento multi-tenant y valida queries para
    prevenir fuga de datos.
    
    Args:
        query: Consulta SQL. Puede ser:
            - String SQL (deprecated, migrar a SQLAlchemy Core)
            - Objeto SQLAlchemy Core (Select, Update, Delete, Insert)
            - TextClause (resultado de text().bindparams())
        params: Parámetros opcionales (tupla o dict). 
            Si es tupla y query tiene '?', se convierte a parámetros nombrados.
        connection_type: Tipo de conexión:
            - DEFAULT: Conexión tenant-aware (usa routing automático)
            - ADMIN: Conexión administrativa (BD central)
        client_id: ID del cliente específico (opcional, puede ser int o UUID).
            Si no se proporciona, se obtiene del contexto de tenant actual.
        skip_tenant_validation: Si True, omite la validación de tenant.
            ⚠️ SOLO funciona si ALLOW_TENANT_FILTER_BYPASS=True en configuración.
            Uso restringido a scripts de migración o mantenimiento.
    
    Returns:
        Lista de diccionarios con los resultados de la query.
        Cada diccionario representa una fila con columnas como claves.
    
    Raises:
        DatabaseError: Si hay error en la ejecución de la query.
        ValidationError: Si skip_tenant_validation=True pero ALLOW_TENANT_FILTER_BYPASS=False.
        SecurityError: Si la query no tiene filtro de tenant y está en producción.
    
    Example:
        ```python
        from sqlalchemy import select
        from app.infrastructure.database.tables import UsuarioTable
        
        # Query con SQLAlchemy Core (recomendado)
        query = select(UsuarioTable).where(UsuarioTable.c.es_activo == True)
        results = await execute_query(query, client_id=current_client_id)
        
        # Query con text() para casos complejos
        from sqlalchemy import text
        query = text("SELECT * FROM usuario WHERE cliente_id = :cliente_id").bindparams(
            cliente_id=current_client_id
        )
        results = await execute_query(query, client_id=current_client_id)
        ```
    
    Note:
        - Para queries string (deprecated), se aplica análisis estático para detectar
          filtros de tenant, pero es menos seguro que SQLAlchemy Core.
        - Se recomienda migrar todas las queries a SQLAlchemy Core para mejor seguridad
          y mantenibilidad.
    """
    # ✅ FASE 1 SEGURIDAD: Validar que skip_tenant_validation solo se use si está permitido
    if skip_tenant_validation:
        if not settings.ALLOW_TENANT_FILTER_BYPASS:
            logger.error(
                f"[SECURITY CRITICAL] Intento de bypass de validación de tenant rechazado. "
                f"skip_tenant_validation=True pero ALLOW_TENANT_FILTER_BYPASS=False. "
                f"Query: {str(query)[:200]}..."
            )
        _assert_skip_tenant_validation_allowed(skip_tenant_validation)
    
    # ✅ FASE 2: Si es objeto SQLAlchemy Core, aplicar filtro de tenant programáticamente
    if isinstance(query, (Select, Update, Delete, Insert)):
        query = _prepare_core_query_for_gateway(
            query,
            client_id=client_id,
            skip_tenant_validation=skip_tenant_validation,
            identity_scope=identity_scope,
        )
        
        # ✅ FASE 5: Gateway unificado resolution → execute
        async with _get_connection_context(
            connection_type,
            client_id,
            operation_class=operation_class,
        ) as session:
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
        query = _prepare_text_clause_for_gateway(
            query,
            client_id=client_id,
            table_name=None,
            skip_tenant_validation=skip_tenant_validation,
            identity_scope=identity_scope,
        )
        
        async with _get_connection_context(
            connection_type,
            client_id,
            operation_class=operation_class,
        ) as session:
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
        
        # ✅ FASE 1 SEGURIDAD: Auditoría automática de queries string
        if not skip_tenant_validation and settings.ENABLE_QUERY_TENANT_VALIDATION:
            table_name = _infer_table_name_from_sql_text(query.lower())
            _run_query_auditor_if_enabled(
                query,
                table_name=table_name,
                client_id=client_id,
                skip_tenant_validation=skip_tenant_validation,
                context_label="string",
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
        # ✅ FASE 1 SEGURIDAD: Aplicar filtro automático de tenant a TextClause
        # Obtener client_id del contexto si está disponible
        from app.core.tenant.context import try_get_current_client_id
        auth_client_id = try_get_current_client_id()
        
        # Intentar extraer nombre de tabla
        try:
            query_str = query.text if hasattr(query, 'text') else str(query)
            query_lower = query_str.lower()
            table_name = None
            
            for keyword in ["from", "update", "delete from", "insert into"]:
                if keyword in query_lower:
                    parts = query_lower.split(keyword, 1)
                    if len(parts) > 1:
                        table_part = parts[1].strip().split()[0].strip(";").strip("(")
                        table_name = table_part
                        break
        except Exception:
            table_name = None
        
        # Aplicar filtro automático si hay contexto de tenant
        if auth_client_id:
            query = apply_tenant_filter_to_text_clause(
                query, 
                client_id=auth_client_id, 
                table_name=table_name
            )
        
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
        # ✅ FASE 1 SEGURIDAD: Aplicar filtro automático de tenant a TextClause
        # Intentar extraer nombre de tabla
        try:
            query_str = query.text if hasattr(query, 'text') else str(query)
            query_lower = query_str.lower()
            table_name = None
            
            for keyword in ["from", "update", "delete from", "insert into"]:
                if keyword in query_lower:
                    parts = query_lower.split(keyword, 1)
                    if len(parts) > 1:
                        table_part = parts[1].strip().split()[0].strip(";").strip("(")
                        table_name = table_part
                        break
        except Exception:
            table_name = None
        
        # Aplicar filtro automático si hay client_id
        if client_id:
            query = apply_tenant_filter_to_text_clause(
                query, 
                client_id=client_id, 
                table_name=table_name
            )
        
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
    client_id: Optional[Union[int, UUID]] = None,
    identity_scope: Optional[IdentityScope] = None,
    operation_class: Optional[str] = None,
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
        query = _prepare_core_query_for_gateway(
            query,
            client_id=client_id,
            skip_tenant_validation=False,
            identity_scope=identity_scope,
        )
        async with _get_connection_context(
            connection_type,
            client_id,
            operation_class=operation_class,
        ) as session:
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
        # ✅ FASE 1 SEGURIDAD: Aplicar filtro automático de tenant a TextClause
        # Intentar extraer nombre de tabla
        try:
            query_str = query.text if hasattr(query, 'text') else str(query)
            query_lower = query_str.lower()
            table_name = None
            
            for keyword in ["from", "update", "delete from", "insert into"]:
                if keyword in query_lower:
                    parts = query_lower.split(keyword, 1)
                    if len(parts) > 1:
                        table_part = parts[1].strip().split()[0].strip(";").strip("(")
                        table_name = table_part
                        break
        except Exception:
            table_name = None
        
        # Aplicar filtro automático si hay client_id
        if client_id:
            query = apply_tenant_filter_to_text_clause(
                query,
                client_id=client_id,
                table_name=table_name,
                identity_scope=identity_scope,
            )
        
        async with _get_connection_context(
            connection_type,
            client_id,
            operation_class=operation_class,
        ) as session:
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
    client_id: Optional[Union[int, UUID]] = None
) -> List[Dict[str, Any]]:
    """
    Ejecuta un stored procedure sin parámetros de forma async.
    
    ✅ FASE 2: Versión async.
    ✅ FASE 1 SEGURIDAD: Validación de cliente_id contra contexto actual.
    
    Args:
        procedure_name: Nombre del stored procedure
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente específico (opcional, puede ser int o UUID).
            Si no se proporciona, se obtiene del contexto de tenant actual.
            Si se proporciona, se valida contra el contexto actual.
    
    Returns:
        Lista de diccionarios con los resultados
    
    Raises:
        SecurityError: Si client_id proporcionado no coincide con contexto actual
    """
    from app.core.tenant.context import try_get_current_client_id
    
    # Obtener client_id del contexto si no se proporciona
    context_client_id = try_get_current_client_id()
    
    if client_id is None:
        client_id = context_client_id
    else:
        # ✅ FASE 1 SEGURIDAD: Validar que client_id proporcionado coincida con contexto
        if context_client_id is not None:
            # Convertir ambos a UUID para comparación
            if isinstance(client_id, int):
                try:
                    client_id_uuid = UUID(int=client_id) if client_id > 0 else None
                except (ValueError, OverflowError):
                    client_id_uuid = None
            elif isinstance(client_id, UUID):
                client_id_uuid = client_id
            else:
                client_id_uuid = None
            
            if client_id_uuid and client_id_uuid != context_client_id:
                logger.error(
                    f"[SECURITY] Intento de ejecutar SP '{procedure_name}' con client_id diferente al contexto. "
                    f"Contexto: {context_client_id}, Proporcionado: {client_id_uuid}"
                )
                raise SecurityError(
                    detail=(
                        f"No se puede ejecutar stored procedure '{procedure_name}' con un cliente_id diferente "
                        f"al contexto actual del tenant. Esto previene acceso cross-tenant."
                    ),
                    internal_code="SP_CLIENT_ID_MISMATCH"
                )
            # Usar el del contexto (más seguro)
            client_id = context_client_id
    
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
    client_id: Optional[Union[int, UUID]] = None
) -> List[Dict[str, Any]]:
    """
    Ejecuta un stored procedure con parámetros nombrados de forma async.
    
    ✅ FASE 2: Versión async.
    ✅ FASE 1 SEGURIDAD: Validación de cliente_id contra contexto actual y parámetros.
    
    Args:
        procedure_name: Nombre del stored procedure
        params_dict: Diccionario con parámetros nombrados (ej: {'UsuarioID': 123, 'ClienteID': uuid})
        connection_type: Tipo de conexión (DEFAULT o ADMIN)
        client_id: ID del cliente específico (opcional, puede ser int o UUID).
            Si no se proporciona, se obtiene del contexto de tenant actual.
            Si se proporciona, se valida contra el contexto actual.
            También se valida que params_dict['ClienteID'] o params_dict['cliente_id'] coincida.
    
    Returns:
        Lista de diccionarios con los resultados
    
    Raises:
        SecurityError: Si client_id proporcionado o en params_dict no coincide con contexto actual
    """
    from app.core.tenant.context import try_get_current_client_id
    
    # Obtener client_id del contexto si no se proporciona
    context_client_id = try_get_current_client_id()
    
    if client_id is None:
        client_id = context_client_id
    else:
        # ✅ FASE 1 SEGURIDAD: Validar que client_id proporcionado coincida con contexto
        if context_client_id is not None:
            # Convertir ambos a UUID para comparación
            if isinstance(client_id, int):
                try:
                    client_id_uuid = UUID(int=client_id) if client_id > 0 else None
                except (ValueError, OverflowError):
                    client_id_uuid = None
            elif isinstance(client_id, UUID):
                client_id_uuid = client_id
            else:
                client_id_uuid = None
            
            if client_id_uuid and client_id_uuid != context_client_id:
                logger.error(
                    f"[SECURITY] Intento de ejecutar SP '{procedure_name}' con client_id diferente al contexto. "
                    f"Contexto: {context_client_id}, Proporcionado: {client_id_uuid}"
                )
                raise SecurityError(
                    detail=(
                        f"No se puede ejecutar stored procedure '{procedure_name}' con un cliente_id diferente "
                        f"al contexto actual del tenant. Esto previene acceso cross-tenant."
                    ),
                    internal_code="SP_CLIENT_ID_MISMATCH"
                )
            # Usar el del contexto (más seguro)
            client_id = context_client_id
    
    # ✅ FASE 1 SEGURIDAD: Validar que params_dict no contenga cliente_id diferente al contexto
    if context_client_id is not None:
        # Buscar cliente_id en params_dict (puede estar como 'ClienteID', 'cliente_id', etc.)
        param_client_id = None
        for key in ['ClienteID', 'cliente_id', 'Cliente_Id', 'CLIENTE_ID']:
            if key in params_dict:
                param_value = params_dict[key]
                # Convertir a UUID si es necesario
                if isinstance(param_value, UUID):
                    param_client_id = param_value
                elif isinstance(param_value, str):
                    try:
                        param_client_id = UUID(param_value)
                    except ValueError:
                        pass
                elif isinstance(param_value, int):
                    try:
                        param_client_id = UUID(int=param_value) if param_value > 0 else None
                    except (ValueError, OverflowError):
                        pass
                break
        
        if param_client_id and param_client_id != context_client_id:
            logger.error(
                f"[SECURITY] Intento de ejecutar SP '{procedure_name}' con cliente_id en params_dict diferente al contexto. "
                f"Contexto: {context_client_id}, En params: {param_client_id}"
            )
            raise SecurityError(
                detail=(
                    f"No se puede ejecutar stored procedure '{procedure_name}' con un cliente_id en los parámetros "
                    f"diferente al contexto actual del tenant. Esto previene acceso cross-tenant."
                ),
                internal_code="SP_PARAMS_CLIENT_ID_MISMATCH"
            )
        
        # ✅ FASE 1 SEGURIDAD: Forzar cliente_id correcto en params_dict si existe la clave
        for key in ['ClienteID', 'cliente_id', 'Cliente_Id', 'CLIENTE_ID']:
            if key in params_dict:
                params_dict[key] = context_client_id
                logger.debug(
                    f"[SECURITY] ClienteID en params_dict forzado a contexto actual: {context_client_id}"
                )
                break
    
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
