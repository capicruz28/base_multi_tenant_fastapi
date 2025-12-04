# app/infrastructure/database/query_helpers.py
"""
Funciones helper para construir queries con SQLAlchemy Core.

✅ FASE 1: Refactorización de acceso a datos
- Funciones programáticas para aplicar filtros de tenant
- Elimina necesidad de análisis de strings SQL
"""

from typing import Optional
from sqlalchemy import Select, Update, Delete, and_, or_
from sqlalchemy.sql import ClauseElement

from app.core.tenant.context import get_current_client_id
from app.core.config import settings
from app.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

# Tablas que NO requieren filtro de tenant (tablas globales/ADMIN)
GLOBAL_TABLES = {
    'cliente',
    'cliente_modulo',
    'modulo',
    'cliente_modulo_activo',
    'cliente_conexion',
    'sistema_config'
}


def apply_tenant_filter(
    query: ClauseElement,
    client_id: Optional[int] = None,
    table_name: Optional[str] = None,
    tenant_column: str = "cliente_id"
) -> ClauseElement:
    """
    Aplica automáticamente el filtro de tenant a una query SQLAlchemy Core.
    
    ✅ FASE 1: Función programática que reemplaza análisis de strings SQL.
    
    Args:
        query: Query SQLAlchemy Core (Select, Update, Delete)
        client_id: ID del cliente (opcional, usa contexto si no se proporciona)
        table_name: Nombre de la tabla (opcional, para verificar si es global)
        tenant_column: Nombre de la columna de tenant (default: "cliente_id")
    
    Returns:
        Query con filtro de tenant aplicado
    
    Raises:
        ValidationError: Si no hay contexto de tenant y no se proporciona client_id
    
    Ejemplo:
        from app.infrastructure.database.tables import UsuarioTable
        from sqlalchemy import select
        
        query = select(UsuarioTable)
        query = apply_tenant_filter(query, table_name="usuario")
        # Resultado: query.where(UsuarioTable.c.cliente_id == current_client_id)
    """
    # Si la tabla es global, no aplicar filtro
    if table_name and table_name.lower() in GLOBAL_TABLES:
        logger.debug(f"[TENANT_FILTER] Tabla '{table_name}' es global, omitiendo filtro de tenant")
        return query
    
    # Obtener client_id
    if client_id is None:
        try:
            client_id = get_current_client_id()
        except RuntimeError:
            # Sin contexto de tenant
            if settings.ALLOW_TENANT_FILTER_BYPASS:
                logger.warning(
                    "[TENANT_FILTER] Sin contexto de tenant pero bypass permitido. "
                    "Query ejecutada sin filtro de tenant."
                )
                return query
            else:
                raise ValidationError(
                    detail=(
                        f"Contexto de tenant OBLIGATORIO para aplicar filtro. "
                        f"Proporcione client_id explícitamente. "
                        f"El filtro {tenant_column} es requerido por seguridad multi-tenant."
                    ),
                    internal_code="TENANT_CONTEXT_REQUIRED"
                )
    
    # Aplicar filtro según tipo de query
    if isinstance(query, Select):
        # SELECT: Agregar WHERE clause
        # Obtener la tabla principal de la query
        from_clause = query.froms[0] if query.froms else None
        
        if from_clause is None:
            logger.warning("[TENANT_FILTER] Query SELECT sin FROM clause, no se puede aplicar filtro")
            return query
        
        # Obtener la columna de tenant de la tabla
        if hasattr(from_clause, 'c'):
            # Es una Table
            tenant_col = getattr(from_clause.c, tenant_column, None)
        elif hasattr(from_clause, 'columns'):
            # Es un Alias u otro tipo
            tenant_col = getattr(from_clause.columns, tenant_column, None)
        else:
            logger.warning(f"[TENANT_FILTER] No se pudo obtener columna {tenant_column} de la tabla")
            return query
        
        if tenant_col is None:
            logger.debug(f"[TENANT_FILTER] Tabla no tiene columna {tenant_column}, omitiendo filtro")
            return query
        
        # Agregar filtro si no existe ya
        # Verificar si ya tiene un filtro de tenant
        if query.whereclause is not None:
            # Verificar si ya incluye el filtro de tenant
            from sqlalchemy import inspect
            for clause in query.whereclause.clauses if hasattr(query.whereclause, 'clauses') else [query.whereclause]:
                if hasattr(clause, 'left') and hasattr(clause, 'right'):
                    if clause.left == tenant_col and clause.right.value == client_id:
                        logger.debug("[TENANT_FILTER] Query ya tiene filtro de tenant, omitiendo")
                        return query
        
        # Aplicar filtro
        query = query.where(tenant_col == client_id)
        logger.debug(f"[TENANT_FILTER] Filtro de tenant aplicado: {tenant_column} = {client_id}")
        
    elif isinstance(query, Update):
        # UPDATE: Agregar WHERE clause
        table = query.table
        if hasattr(table, 'c'):
            tenant_col = getattr(table.c, tenant_column, None)
            if tenant_col is not None:
                if query.whereclause is not None:
                    query = query.where(and_(query.whereclause, tenant_col == client_id))
                else:
                    query = query.where(tenant_col == client_id)
                logger.debug(f"[TENANT_FILTER] Filtro de tenant aplicado a UPDATE: {tenant_column} = {client_id}")
        
    elif isinstance(query, Delete):
        # DELETE: Agregar WHERE clause
        table = query.table
        if hasattr(table, 'c'):
            tenant_col = getattr(table.c, tenant_column, None)
            if tenant_col is not None:
                if query.whereclause is not None:
                    query = query.where(and_(query.whereclause, tenant_col == client_id))
                else:
                    query = query.where(tenant_col == client_id)
                logger.debug(f"[TENANT_FILTER] Filtro de tenant aplicado a DELETE: {tenant_column} = {client_id}")
    
    return query


def get_table_name_from_query(query: ClauseElement) -> Optional[str]:
    """
    Extrae el nombre de la tabla de una query SQLAlchemy Core.
    
    Args:
        query: Query SQLAlchemy Core
    
    Returns:
        Nombre de la tabla o None si no se puede determinar
    """
    if isinstance(query, (Select, Update, Delete)):
        if hasattr(query, 'table'):
            table = query.table
            if hasattr(table, 'name'):
                return table.name
            elif hasattr(table, 'original'):
                return getattr(table.original, 'name', None)
        elif hasattr(query, 'froms') and query.froms:
            from_clause = query.froms[0]
            if hasattr(from_clause, 'name'):
                return from_clause.name
            elif hasattr(from_clause, 'original'):
                return getattr(from_clause.original, 'name', None)
    
    return None




