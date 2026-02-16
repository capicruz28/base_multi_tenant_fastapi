# app/infrastructure/database/query_helpers.py
"""
Helpers para queries SQL.

✅ FASE 1: Funciones programáticas para aplicar filtros de tenant.
✅ FASE 4C: Migrado get_user_complete_data_query desde queries.py.
"""

import logging
from typing import Optional, Any, Union
from uuid import UUID
from sqlalchemy import Select, Update, Delete, and_
from sqlalchemy.sql import ClauseElement

from app.infrastructure.database.sql_constants import (
    GET_USER_COMPLETE_OPTIMIZED_JSON,
    GET_USER_COMPLETE_OPTIMIZED_XML
)
from app.core.tenant.context import try_get_current_client_id
from app.core.exceptions import ValidationError
from app.core.config import settings

logger = logging.getLogger(__name__)

# Tablas globales que no requieren filtro de tenant
GLOBAL_TABLES = {
    'cliente',
    'cliente_modulo',
    'cliente_conexion',
    'sistema_config'
}

# Cache de versión de SQL Server (se detecta una vez)
_sql_server_version_cache: Optional[int] = None


def apply_tenant_filter(
    query: ClauseElement,
    client_id: Optional[Union[int, UUID]] = None,
    table_name: Optional[str] = None,
    tenant_column: str = "cliente_id"
) -> ClauseElement:
    """
    Aplica filtro de tenant automáticamente a queries SQLAlchemy Core.
    
    ✅ FASE 1: Función programática que reemplaza análisis de strings SQL.
    
    Args:
        query: Query SQLAlchemy Core (Select, Update, Delete)
        client_id: ID del cliente (opcional, usa contexto si no se proporciona)
        table_name: Nombre de la tabla (opcional, se infiere si es posible)
        tenant_column: Nombre de la columna de tenant (default: "cliente_id")
    
    Returns:
        Query con filtro de tenant aplicado
    
    Raises:
        ValidationError: Si no hay contexto ni client_id y bypass no está permitido
    """
    # ✅ CORRECCIÓN: Obtener nombre de tabla PRIMERO para verificar si es global
    # Si es tabla global, no necesita client_id ni filtro de tenant
    if table_name is None:
        table_name = get_table_name_from_query(query)
    
    # Si es tabla global, no aplicar filtro (no requiere client_id)
    if table_name and table_name.lower() in GLOBAL_TABLES:
        logger.debug(f"[TENANT_FILTER] Tabla global '{table_name}' detectada, omitiendo filtro")
        return query
    
    # Obtener client_id solo si NO es tabla global
    if client_id is None:
        client_id = try_get_current_client_id()
    
    # Si no hay client_id y no está permitido el bypass, error
    if client_id is None:
        if not settings.ALLOW_TENANT_FILTER_BYPASS:
            raise ValidationError(
                detail="No se puede aplicar filtro de tenant: falta client_id y contexto",
                internal_code="MISSING_TENANT_CONTEXT"
            )
        logger.warning("[TENANT_FILTER] Ejecutando query sin filtro de tenant (bypass permitido)")
        return query
    
    # Aplicar filtro según tipo de query
    if isinstance(query, Select):
        # Obtener tabla de la query
        from_clause = query.froms[0] if query.froms else None
        if from_clause is None:
            return query
        
        # Verificar si ya tiene filtro de tenant
        # (simplificado: asumimos que no lo tiene y lo agregamos)
        tenant_col = getattr(from_clause.c, tenant_column, None)
        if tenant_col is not None:
            # Agregar condición WHERE
            if query.whereclause is None:
                query = query.where(tenant_col == client_id)
            else:
                query = query.where(and_(query.whereclause, tenant_col == client_id))
    
    elif isinstance(query, (Update, Delete)):
        # Para Update/Delete, agregar condición WHERE
        from_clause = query.table if hasattr(query, 'table') else None
        if from_clause is None:
            return query
        
        tenant_col = getattr(from_clause.c, tenant_column, None)
        if tenant_col is not None:
            if query.whereclause is None:
                query = query.where(tenant_col == client_id)
            else:
                query = query.where(and_(query.whereclause, tenant_col == client_id))
    
    return query


def get_table_name_from_query(query: ClauseElement) -> Optional[str]:
    """
    Extrae el nombre de la tabla de una query SQLAlchemy Core.
    
    ✅ FASE 1: Helper para determinar si es tabla global.
    
    Args:
        query: Query SQLAlchemy Core
    
    Returns:
        Nombre de la tabla o None si no se puede determinar
    """
    try:
        if isinstance(query, Select):
            if query.froms:
                table = query.froms[0]
                return getattr(table, 'name', None) or str(table)
        elif isinstance(query, (Update, Delete)):
            if hasattr(query, 'table'):
                table = query.table
                return getattr(table, 'name', None) or str(table)
    except Exception as e:
        logger.debug(f"[TABLE_NAME] Error extrayendo nombre de tabla: {e}")
    
    return None


def get_user_complete_data_query(use_json: bool = True) -> str:
    """
    Retorna la query apropiada según la versión de SQL Server.
    
    ✅ FASE 4C: Migrado desde queries.py para eliminar dependencias deprecated.
    
    Args:
        use_json: Si True, usa query JSON (SQL Server 2016+). Si False, usa XML (compatible).
    
    Returns:
        str: Query SQL apropiada
    """
    if use_json:
        logger.debug("[QUERY_HELPER] Usando query JSON (SQL Server 2016+)")
        return GET_USER_COMPLETE_OPTIMIZED_JSON
    else:
        logger.debug("[QUERY_HELPER] Usando query XML (compatible con SQL Server 2005+)")
        return GET_USER_COMPLETE_OPTIMIZED_XML
