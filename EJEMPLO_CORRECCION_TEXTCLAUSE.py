"""
EJEMPLO PRÁCTICO: Corrección de Queries TextClause Sin Filtro Automático

Este archivo muestra cómo implementar la solución para aplicar filtro automático
a queries TextClause, protegiendo contra fuga de datos entre tenants.
"""

from sqlalchemy import text, TextClause
from typing import Optional, Union
from uuid import UUID
import re
import logging

from app.core.tenant.context import try_get_current_client_id
from app.core.exceptions import ValidationError
from app.core.config import settings

logger = logging.getLogger(__name__)

# Tablas globales que no requieren filtro de tenant
GLOBAL_TABLES = {
    'cliente',
    'cliente_modulo',
    'cliente_conexion',
    'sistema_config',
    'modulo',  # Catálogo global
    'modulo_seccion'  # Catálogo global
}


def apply_tenant_filter_to_text_clause(
    query: TextClause,
    client_id: Optional[Union[int, UUID]] = None,
    table_name: Optional[str] = None,
    tenant_column: str = "cliente_id"
) -> TextClause:
    """
    Aplica filtro de tenant automáticamente a TextClause.
    
    ✅ SOLUCIÓN: Intenta parsear el SQL y agregar filtro de cliente_id si no existe.
    
    Args:
        query: TextClause a modificar
        client_id: ID del cliente (opcional, usa contexto si no se proporciona)
        table_name: Nombre de la tabla (opcional, se infiere si es posible)
        tenant_column: Nombre de la columna de tenant (default: "cliente_id")
    
    Returns:
        TextClause modificado con filtro de tenant
    
    Example:
        ```python
        from sqlalchemy import text
        
        # Query sin filtro de tenant
        query = text("SELECT * FROM usuario WHERE es_activo = 1").bindparams()
        
        # Aplicar filtro automático
        query_protegida = apply_tenant_filter_to_text_clause(query, client_id=cliente_id)
        # Resultado: "SELECT * FROM usuario WHERE es_activo = 1 AND cliente_id = :cliente_id"
        ```
    """
    # Obtener client_id si no se proporciona
    if client_id is None:
        client_id = try_get_current_client_id()
    
    if client_id is None:
        if not settings.ALLOW_TENANT_FILTER_BYPASS:
            raise ValidationError(
                detail="No se puede aplicar filtro de tenant: falta client_id y contexto",
                internal_code="MISSING_TENANT_CONTEXT"
            )
        logger.warning("[TENANT_FILTER] Ejecutando TextClause sin filtro de tenant (bypass permitido)")
        return query
    
    # Obtener SQL string del TextClause
    # Intentar obtener el texto SQL original
    try:
        # TextClause tiene un atributo _text que contiene el SQL original
        query_str = query.text if hasattr(query, 'text') else str(query)
    except Exception:
        query_str = str(query)
    
    query_lower = query_str.lower()
    
    # Extraer nombre de tabla si no se proporciona
    if table_name is None:
        table_name = _extract_table_name_from_sql(query_str, query_lower)
    
    # Si es tabla global, no aplicar filtro
    if table_name and table_name.lower() in GLOBAL_TABLES:
        logger.debug(f"[TENANT_FILTER] Tabla global '{table_name}' detectada, omitiendo filtro")
        return query
    
    # Verificar si ya tiene filtro de tenant
    if _has_tenant_filter(query_str, tenant_column, client_id):
        logger.debug(f"[TENANT_FILTER] TextClause ya tiene filtro de tenant")
        return query
    
    # Agregar filtro de tenant
    modified_query_str = _add_tenant_filter_to_sql(
        query_str, 
        tenant_column, 
        client_id
    )
    
    # Obtener parámetros existentes y agregar cliente_id
    existing_params = {}
    if hasattr(query, 'bindparams'):
        # Extraer parámetros del TextClause
        for key in query.bindparams.keys():
            existing_params[key] = query.bindparams[key].value
    
    # Agregar cliente_id a los parámetros
    existing_params[tenant_column] = client_id
    
    # Crear nuevo TextClause con filtro agregado
    new_query = text(modified_query_str).bindparams(**existing_params)
    
    logger.debug(
        f"[TENANT_FILTER] Filtro de tenant agregado automáticamente a TextClause. "
        f"Tabla: {table_name}"
    )
    
    return new_query


def _extract_table_name_from_sql(query_str: str, query_lower: str) -> Optional[str]:
    """
    Extrae el nombre de la tabla principal de una query SQL.
    
    Busca patrones: "FROM tabla", "UPDATE tabla", "DELETE FROM tabla", "INSERT INTO tabla"
    """
    # Buscar patrones comunes
    patterns = [
        (r'\bfrom\s+(\w+)', 'from'),
        (r'\bupdate\s+(\w+)', 'update'),
        (r'\bdelete\s+from\s+(\w+)', 'delete'),
        (r'\binsert\s+into\s+(\w+)', 'insert'),
    ]
    
    for pattern, keyword in patterns:
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            # Limpiar nombre de tabla (puede tener esquema: esquema.tabla)
            if '.' in table_name:
                table_name = table_name.split('.')[-1]
            return table_name.strip()
    
    return None


def _has_tenant_filter(query_str: str, tenant_column: str, client_id: Union[int, UUID]) -> bool:
    """
    Verifica si la query ya tiene filtro de tenant.
    
    Busca patrones como:
    - cliente_id = :cliente_id
    - cliente_id = :client_id
    - cliente_id = <valor>
    """
    patterns = [
        f"{tenant_column}\\s*=\\s*:{tenant_column}",
        f"{tenant_column}\\s*=\\s*:client_id",
        f"{tenant_column}\\s*=\\s*{client_id}",
        f"{tenant_column}\\s*=\\s*'{client_id}'",
        f"{tenant_column}\\s*=\\s*\"{client_id}\"",
    ]
    
    for pattern in patterns:
        if re.search(pattern, query_str, re.IGNORECASE):
            return True
    
    return False


def _add_tenant_filter_to_sql(
    query_str: str, 
    tenant_column: str, 
    client_id: Union[int, UUID]
) -> str:
    """
    Agrega filtro de tenant a una query SQL.
    
    Si tiene WHERE, agrega "AND cliente_id = :cliente_id"
    Si no tiene WHERE, agrega "WHERE cliente_id = :cliente_id"
    """
    query_lower = query_str.lower()
    
    if "where" in query_lower:
        # Ya tiene WHERE, agregar AND cliente_id = :cliente_id
        # Buscar el último WHERE (puede haber subqueries)
        where_matches = list(re.finditer(r'\bwhere\b', query_lower))
        if where_matches:
            # Usar el último WHERE (más probable que sea el principal)
            last_where = where_matches[-1]
            where_pos = last_where.end()
            
            # Encontrar el final del WHERE clause (puede tener ORDER BY, GROUP BY, etc.)
            # Buscar el siguiente keyword que termine el WHERE
            end_keywords = ['order by', 'group by', 'having', 'limit', 'offset', ';']
            end_pos = len(query_str)
            
            for keyword in end_keywords:
                keyword_pos = query_lower.find(keyword, where_pos)
                if keyword_pos != -1 and keyword_pos < end_pos:
                    end_pos = keyword_pos
            
            # Insertar filtro antes del final
            filter_clause = f" AND {tenant_column} = :{tenant_column}"
            modified_query = (
                query_str[:end_pos] + 
                filter_clause + 
                query_str[end_pos:]
            )
            return modified_query
    else:
        # No tiene WHERE, agregar WHERE cliente_id = :cliente_id
        # Buscar FROM para determinar dónde insertar
        from_match = re.search(r'\bfrom\s+(\w+)', query_lower, re.IGNORECASE)
        if from_match:
            from_pos = from_match.end()
            
            # Encontrar el final de la tabla (puede tener JOIN, etc.)
            # Buscar el siguiente keyword o punto y coma
            end_keywords = ['where', 'order by', 'group by', 'having', 'limit', 'offset', ';']
            end_pos = len(query_str)
            
            for keyword in end_keywords:
                keyword_pos = query_lower.find(keyword, from_pos)
                if keyword_pos != -1 and keyword_pos < end_pos:
                    end_pos = keyword_pos
            
            # Insertar WHERE antes del final
            filter_clause = f" WHERE {tenant_column} = :{tenant_column}"
            modified_query = (
                query_str[:end_pos] + 
                filter_clause + 
                query_str[end_pos:]
            )
            return modified_query
    
    # Si no se pudo modificar, retornar original (con advertencia)
    logger.warning(
        f"[TENANT_FILTER] No se pudo aplicar filtro automático a TextClause. "
        f"Query: {query_str[:200]}..."
    )
    return query_str


# ============================================
# EJEMPLO DE USO
# ============================================

def ejemplo_uso():
    """
    Ejemplo de cómo usar apply_tenant_filter_to_text_clause()
    """
    from uuid import UUID
    
    cliente_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    
    # Ejemplo 1: Query sin filtro de tenant (VULNERABLE)
    query_vulnerable = text("""
        SELECT usuario_id, nombre_usuario, correo
        FROM usuario
        WHERE es_activo = 1
          AND correo = :correo
    """).bindparams(correo="usuario@example.com")
    
    # Aplicar filtro automático
    query_protegida = apply_tenant_filter_to_text_clause(
        query_vulnerable, 
        client_id=cliente_id
    )
    
    print("Query original:")
    print(query_vulnerable.text)
    print("\nQuery protegida:")
    print(query_protegida.text)
    print("\nParámetros:")
    print(query_protegida.bindparams)
    
    # Resultado esperado:
    # Query protegida: "SELECT ... WHERE es_activo = 1 AND correo = :correo AND cliente_id = :cliente_id"
    # Parámetros: {'correo': 'usuario@example.com', 'cliente_id': <UUID>}
    
    # Ejemplo 2: Query que ya tiene filtro de tenant (no se modifica)
    query_con_filtro = text("""
        SELECT usuario_id, nombre_usuario
        FROM usuario
        WHERE es_activo = 1
          AND cliente_id = :cliente_id
    """).bindparams(cliente_id=cliente_id)
    
    query_sin_cambios = apply_tenant_filter_to_text_clause(
        query_con_filtro,
        client_id=cliente_id
    )
    
    print("\n\nQuery con filtro existente (no se modifica):")
    print(query_sin_cambios.text)
    
    # Ejemplo 3: Query sobre tabla global (no se aplica filtro)
    query_global = text("""
        SELECT cliente_id, codigo_cliente, razon_social
        FROM cliente
        WHERE es_activo = 1
    """)
    
    query_global_protegida = apply_tenant_filter_to_text_clause(
        query_global,
        client_id=cliente_id
    )
    
    print("\n\nQuery sobre tabla global (no se aplica filtro):")
    print(query_global_protegida.text)


if __name__ == "__main__":
    ejemplo_uso()
