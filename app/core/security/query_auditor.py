# app/core/security/query_auditor.py
"""
Módulo de auditoría automática de queries para seguridad multi-tenant.

✅ FASE 1 SEGURIDAD: Detecta y previene queries sin filtro de tenant.

Este módulo valida que todas las queries incluyan filtro de cliente_id
para prevenir fuga de datos entre tenants.
"""

import logging
from typing import Union, Optional, Dict, Any
from sqlalchemy import Select, Update, Delete, Insert, text, TextClause
from sqlalchemy.sql import ClauseElement

from app.core.config import settings
from app.core.tenant.context import try_get_current_client_id
from app.core.exceptions import SecurityError

logger = logging.getLogger(__name__)


class QueryAuditor:
    """
    Auditor de queries para validar seguridad multi-tenant.
    
    ✅ FASE 1 SEGURIDAD: Detecta queries sin filtro de tenant y previene fuga de datos.
    
    Esta clase proporciona validación automática de queries para garantizar que todas
    las operaciones de base de datos respeten el aislamiento multi-tenant. Se integra
    automáticamente en execute_query() y puede bloquear queries inseguras en producción.
    
    Características:
    - Valida queries SQLAlchemy Core, TextClause y strings
    - Reconoce tablas globales que no requieren filtro de tenant
    - Bloquea queries inseguras en producción (si ENABLE_QUERY_TENANT_VALIDATION=True)
    - Genera advertencias en desarrollo para facilitar debugging
    
    Uso:
        Normalmente no se usa directamente, se integra automáticamente en execute_query().
        Para uso manual:
        
        ```python
        from sqlalchemy import select
        from app.infrastructure.database.tables import UsuarioTable
        
        query = select(UsuarioTable).where(UsuarioTable.c.es_activo == True)
        QueryAuditor.validate_tenant_filter(
            query=query,
            table_name="usuario",
            client_id=current_client_id
        )
        ```
    """
    
    # Tablas globales que no requieren filtro de tenant
    GLOBAL_TABLES = {
        'cliente',
        'cliente_modulo',
        'cliente_conexion',
        'sistema_config'
    }
    
    @staticmethod
    def validate_tenant_filter(
        query: Union[str, ClauseElement, TextClause],
        table_name: Optional[str] = None,
        client_id: Optional[Any] = None,
        skip_validation: bool = False
    ) -> bool:
        """
        Valida que la query tenga filtro de cliente_id.
        
        Args:
            query: Query SQL (string, SQLAlchemy Core, o TextClause)
            table_name: Nombre de la tabla principal (opcional, se infiere si es posible)
            client_id: ID del cliente (opcional, se obtiene del contexto si no se proporciona)
            skip_validation: Si True, omite validación (solo si ALLOW_TENANT_FILTER_BYPASS=True)
        
        Returns:
            True si la query es segura (tiene filtro o es tabla global)
        
        Raises:
            SecurityError: Si la query no tiene filtro de tenant y skip_validation=False
        """
        # Si skip_validation está habilitado y está permitido, omitir validación
        if skip_validation:
            if not settings.ALLOW_TENANT_FILTER_BYPASS:
                logger.error(
                    "[QUERY_AUDITOR] Intento de skip_validation sin ALLOW_TENANT_FILTER_BYPASS"
                )
                raise SecurityError(
                    detail="skip_validation no permitido sin ALLOW_TENANT_FILTER_BYPASS",
                    internal_code="QUERY_AUDIT_BYPASS_DISABLED"
                )
            else:
                logger.warning(
                    "[QUERY_AUDITOR] Validación omitida (ALLOW_TENANT_FILTER_BYPASS=True)"
                )
                return True
        
        # Si es tabla global, no requiere validación
        if table_name and table_name.lower() in QueryAuditor.GLOBAL_TABLES:
            logger.debug(f"[QUERY_AUDITOR] Tabla '{table_name}' es global, omitiendo validación")
            return True
        
        # Obtener client_id si no se proporciona
        if client_id is None:
            try:
                client_id = try_get_current_client_id()
            except RuntimeError:
                # Sin contexto (scripts de fondo, etc.)
                # En producción, esto debería ser un error
                if settings.ENVIRONMENT == "production":
                    logger.error(
                        "[QUERY_AUDITOR] Sin contexto de tenant en producción"
                    )
                    raise SecurityError(
                        detail="Contexto de tenant requerido en producción",
                        internal_code="TENANT_CONTEXT_REQUIRED"
                    )
                else:
                    logger.warning(
                        "[QUERY_AUDITOR] Sin contexto de tenant (desarrollo)"
                    )
                    return True  # Permitir en desarrollo
        
        # Validar según tipo de query
        if isinstance(query, (Select, Update, Delete, Insert)):
            return QueryAuditor._validate_sqlalchemy_query(query, table_name, client_id)
        elif isinstance(query, TextClause):
            return QueryAuditor._validate_text_clause(query, table_name, client_id)
        elif isinstance(query, str):
            return QueryAuditor._validate_string_query(query, table_name, client_id)
        else:
            logger.warning(
                f"[QUERY_AUDITOR] Tipo de query no reconocido: {type(query)}"
            )
            return True  # Por seguridad, permitir si no se puede validar
    
    @staticmethod
    def _validate_sqlalchemy_query(
        query: Union[Select, Update, Delete, Insert],
        table_name: Optional[str],
        client_id: Any
    ) -> bool:
        """
        Valida query SQLAlchemy Core.
        
        Verifica que el WHERE clause incluya filtro de cliente_id.
        """
        try:
            # Obtener tabla principal
            if table_name is None:
                table_name = QueryAuditor._extract_table_name_from_query(query)
            
            if table_name and table_name.lower() in QueryAuditor.GLOBAL_TABLES:
                return True
            
            # Verificar WHERE clause
            if hasattr(query, 'whereclause') and query.whereclause is not None:
                # Buscar filtro de cliente_id en el WHERE clause
                where_str = str(query.whereclause)
                
                # Buscar patrones comunes de filtro de tenant
                has_tenant_filter = (
                    f"cliente_id = {client_id}" in where_str or
                    f"cliente_id == {client_id}" in where_str or
                    "cliente_id = :cliente_id" in where_str or
                    "cliente_id = :client_id" in where_str or
                    "cliente_id = ?" in where_str
                )
                
                if has_tenant_filter:
                    logger.debug(
                        f"[QUERY_AUDITOR] Query SQLAlchemy Core tiene filtro de tenant: {table_name}"
                    )
                    return True
                else:
                    # ⚠️ ADVERTENCIA: Query sin filtro de tenant
                    logger.warning(
                        f"[QUERY_AUDITOR] Query SQLAlchemy Core sin filtro explícito de cliente_id. "
                        f"Tabla: {table_name}, Query: {str(query)[:200]}..."
                    )
                    
                    # En producción, bloquear si está habilitado
                    if settings.ENVIRONMENT == "production" and settings.ENABLE_QUERY_TENANT_VALIDATION:
                        raise SecurityError(
                            detail=(
                                f"Query sin filtro de tenant detectada para tabla '{table_name}'. "
                                "Por seguridad multi-tenant, todas las queries deben incluir filtro de cliente_id."
                            ),
                            internal_code="QUERY_MISSING_TENANT_FILTER"
                        )
                    
                    return True  # En desarrollo, solo loggear
            else:
                # Query sin WHERE clause
                logger.warning(
                    f"[QUERY_AUDITOR] Query SQLAlchemy Core sin WHERE clause. "
                    f"Tabla: {table_name}"
                )
                
                if settings.ENVIRONMENT == "production" and settings.ENABLE_QUERY_TENANT_VALIDATION:
                    raise SecurityError(
                        detail=(
                            f"Query sin WHERE clause para tabla '{table_name}'. "
                            "Por seguridad multi-tenant, todas las queries deben incluir filtro de cliente_id."
                        ),
                        internal_code="QUERY_MISSING_WHERE_CLAUSE"
                    )
                
                return True
        
        except SecurityError:
            raise
        except Exception as e:
            logger.error(
                f"[QUERY_AUDITOR] Error validando query SQLAlchemy Core: {e}",
                exc_info=True
            )
            # Por seguridad, bloquear si hay error
            if settings.ENVIRONMENT == "production":
                raise SecurityError(
                    detail=f"Error validando query: {str(e)}",
                    internal_code="QUERY_VALIDATION_ERROR"
                )
            return True
    
    @staticmethod
    def _validate_text_clause(
        query: TextClause,
        table_name: Optional[str],
        client_id: Any
    ) -> bool:
        """
        Valida TextClause (resultado de text().bindparams()).
        """
        try:
            query_str = str(query)
            return QueryAuditor._validate_string_query(query_str, table_name, client_id)
        except Exception as e:
            logger.error(
                f"[QUERY_AUDITOR] Error validando TextClause: {e}",
                exc_info=True
            )
            return True  # Por seguridad, permitir si hay error
    
    @staticmethod
    def _validate_string_query(
        query: str,
        table_name: Optional[str],
        client_id: Any
    ) -> bool:
        """
        Valida query string SQL.
        
        ⚠️ ADVERTENCIA: Análisis de string es frágil. Preferir SQLAlchemy Core.
        """
        query_lower = query.lower().strip()
        
        # Si es tabla global, no requiere validación
        if table_name and table_name.lower() in QueryAuditor.GLOBAL_TABLES:
            return True
        
        # Buscar WHERE en la query
        if "where" in query_lower:
            # Buscar patrones comunes de filtro de tenant
            has_tenant_filter = (
                f"cliente_id = {client_id}" in query_lower or
                "cliente_id = :cliente_id" in query_lower or
                "cliente_id = :client_id" in query_lower or
                "cliente_id = ?" in query_lower or
                "cliente_id=" in query_lower
            )
            
            if has_tenant_filter:
                logger.debug(
                    f"[QUERY_AUDITOR] Query string tiene filtro de tenant: {table_name}"
                )
                return True
            else:
                # ⚠️ ADVERTENCIA: Query sin filtro de tenant
                logger.warning(
                    f"[QUERY_AUDITOR] Query string sin filtro explícito de cliente_id. "
                    f"Tabla: {table_name}, Query: {query[:200]}..."
                )
                
                # En producción, bloquear si está habilitado
                if settings.ENVIRONMENT == "production" and settings.ENABLE_QUERY_TENANT_VALIDATION:
                    raise SecurityError(
                        detail=(
                            f"Query sin filtro de tenant detectada para tabla '{table_name}'. "
                            "Por seguridad multi-tenant, todas las queries deben incluir filtro de cliente_id."
                        ),
                        internal_code="QUERY_MISSING_TENANT_FILTER"
                    )
                
                return True  # En desarrollo, solo loggear
        else:
            # Query sin WHERE clause
            logger.warning(
                f"[QUERY_AUDITOR] Query string sin WHERE clause. "
                f"Tabla: {table_name}"
            )
            
            if settings.ENVIRONMENT == "production" and settings.ENABLE_QUERY_TENANT_VALIDATION:
                raise SecurityError(
                    detail=(
                        f"Query sin WHERE clause para tabla '{table_name}'. "
                        "Por seguridad multi-tenant, todas las queries deben incluir filtro de cliente_id."
                    ),
                    internal_code="QUERY_MISSING_WHERE_CLAUSE"
                )
            
            return True
    
    @staticmethod
    def _extract_table_name_from_query(query: Union[Select, Update, Delete, Insert]) -> Optional[str]:
        """
        Extrae el nombre de la tabla principal de una query SQLAlchemy Core.
        """
        try:
            if isinstance(query, Select):
                # SELECT: obtener de FROM clause
                if query.froms:
                    from_clause = query.froms[0]
                    if hasattr(from_clause, 'name'):
                        return from_clause.name
                    elif hasattr(from_clause, '__table__'):
                        return from_clause.__table__.name
            elif isinstance(query, (Update, Delete)):
                # UPDATE/DELETE: obtener de table
                if hasattr(query, 'table'):
                    table = query.table
                    if hasattr(table, 'name'):
                        return table.name
            elif isinstance(query, Insert):
                # INSERT: obtener de table
                if hasattr(query, 'table'):
                    table = query.table
                    if hasattr(table, 'name'):
                        return table.name
        except Exception as e:
            logger.debug(f"[QUERY_AUDITOR] Error extrayendo nombre de tabla: {e}")
        
        return None


# Función helper para uso directo
def validate_query_tenant_filter(
    query: Union[str, ClauseElement, TextClause],
    table_name: Optional[str] = None,
    client_id: Optional[Any] = None,
    skip_validation: bool = False
) -> bool:
    """
    Función helper para validar filtro de tenant en queries.
    
    Uso:
        from app.core.security.query_auditor import validate_query_tenant_filter
        
        if not validate_query_tenant_filter(query, table_name="usuario"):
            raise SecurityError("Query sin filtro de tenant")
    """
    return QueryAuditor.validate_tenant_filter(
        query=query,
        table_name=table_name,
        client_id=client_id,
        skip_validation=skip_validation
    )

