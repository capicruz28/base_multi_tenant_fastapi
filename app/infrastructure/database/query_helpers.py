# app/infrastructure/database/query_helpers.py
"""
Helpers para queries SQL.

✅ FASE 1: Funciones programáticas para aplicar filtros de tenant.
✅ FASE 4C: Migrado get_user_complete_data_query desde queries.py.

Política tenant filter (TD-08 / ADR-006 / RI-40):
- Shared (tenant_data): enforce `cliente_id` en tablas no globales — siempre.
- Dedicated (tenant_data): filter defensivo obligatorio — no sustituye aislamiento
  físico pero previene regresiones si la ruta es incorrecta (wrong-route).
- GLOBAL_TABLES: sin filtro en shared y dedicated.
- control_plane / bypass scripts: sin cambio de contrato público.
"""

import logging
import re
from typing import Optional, Any, Union, Iterable, Set, FrozenSet
from uuid import UUID
from sqlalchemy import Select, Update, Delete, and_, text, TextClause
from sqlalchemy.sql import ClauseElement
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, Grouping
from sqlalchemy.sql.schema import Table
from sqlalchemy.sql.selectable import Join

from app.core.identity.identity_scope import IdentityScope
from app.infrastructure.database.sql_constants import (
    GET_USER_COMPLETE_OPTIMIZED_JSON,
    GET_USER_COMPLETE_OPTIMIZED_XML
)
from app.core.tenant.context import try_get_current_client_id, try_get_tenant_context
from app.core.exceptions import ValidationError, SecurityError
from app.core.config import settings

logger = logging.getLogger(__name__)

INSTALLATION_MODE_DEDICATED = "dedicated"
DEFENSIVE_TENANT_FILTER_REQUIRED = "DEFENSIVE_TENANT_FILTER_REQUIRED"

# Tablas globales que no requieren filtro de tenant
GLOBAL_TABLES = {
    'cliente',
    'cliente_modulo',
    'cliente_conexion',
    'sistema_config',
    'modulo',  # Catálogo global
    'modulo_seccion',  # Catálogo global
    'modulo_menu',  # Catálogo global (aunque puede tener cliente_id para personalización)
    'permiso',  # Catálogo global RBAC (solo en BD central)
    # Catálogos globales en BD dedicada (no tienen cliente_id)
    'cat_moneda',
    'cat_pais',
    'cat_departamento',
    'cat_provincia',
    'cat_distrito',
}

# Cache de versión de SQL Server (se detecta una vez)
_sql_server_version_cache: Optional[int] = None


def _is_dedicated_tenant_context() -> bool:
    """TD-08: dedicated explícito vía TenantContext (database_type multi o tipo_instalacion)."""
    ctx = try_get_tenant_context()
    if ctx is None:
        return False
    if ctx.database_type == "multi":
        return True
    return ctx.tipo_instalacion == INSTALLATION_MODE_DEDICATED


def _all_tables_are_global(table_names: Iterable[str]) -> bool:
    names = {name.lower() for name in table_names if name}
    return bool(names) and names.issubset(GLOBAL_TABLES)


def collect_base_table_names_from_clause(clause: Any) -> FrozenSet[str]:
    """Recorre Join/Table y devuelve nombres base (sin alias compuesto)."""
    if clause is None:
        return frozenset()
    if isinstance(clause, Table):
        name = getattr(clause, "name", None)
        return frozenset({name.lower()}) if name else frozenset()
    if isinstance(clause, Join):
        left = collect_base_table_names_from_clause(clause.left)
        right = collect_base_table_names_from_clause(clause.right)
        return frozenset(set(left) | set(right))
    name = getattr(clause, "name", None)
    if name and isinstance(name, str) and " JOIN " not in name.upper():
        return frozenset({name.lower()})
    return frozenset()


def collect_base_table_names_from_query(query: ClauseElement) -> FrozenSet[str]:
    names: Set[str] = set()
    try:
        if isinstance(query, Select):
            froms = (
                query.get_final_froms()
                if hasattr(query, "get_final_froms")
                else query.froms
            )
            for from_clause in froms or []:
                names.update(collect_base_table_names_from_clause(from_clause))
        elif isinstance(query, (Update, Delete)):
            if hasattr(query, "table"):
                names.update(collect_base_table_names_from_clause(query.table))
    except Exception as exc:
        logger.debug("[TABLE_NAME] Error recopilando tablas base: %s", exc)
    return frozenset(names)


def _iter_binary_clauses(clause: Any):
    if clause is None:
        return
    if isinstance(clause, BooleanClauseList):
        for child in clause.clauses:
            yield from _iter_binary_clauses(child)
    elif isinstance(clause, Grouping):
        yield from _iter_binary_clauses(clause.element)
    elif isinstance(clause, BinaryExpression):
        yield clause


def _clause_references_tenant_column(
    clause: BinaryExpression,
    tenant_column: str,
) -> bool:
    left_key = getattr(clause.left, "key", None)
    right_key = getattr(clause.right, "key", None)
    return left_key == tenant_column or right_key == tenant_column


def _select_has_explicit_tenant_predicate(
    query: Select,
    tenant_column: str = "cliente_id",
) -> bool:
    for clause in _iter_binary_clauses(query.whereclause):
        if _clause_references_tenant_column(clause, tenant_column):
            return True
    froms = (
        query.get_final_froms()
        if hasattr(query, "get_final_froms")
        else query.froms
    )
    for from_clause in froms or []:
        if isinstance(from_clause, Join):
            for clause in _iter_binary_clauses(from_clause.onclause):
                if _clause_references_tenant_column(clause, tenant_column):
                    return True
    return False


def _first_base_table_name(clause: Any) -> Optional[str]:
    if clause is None:
        return None
    if isinstance(clause, Table):
        return getattr(clause, "name", None)
    if isinstance(clause, Join):
        left_name = _first_base_table_name(clause.left)
        if left_name:
            return left_name
        return _first_base_table_name(clause.right)
    return getattr(clause, "name", None)


def _raise_defensive_tenant_filter_required(
    table_name: Optional[str],
    reason: str,
) -> None:
    raise SecurityError(
        detail=(
            f"Filter defensivo cliente_id obligatorio en dedicated (TD-08). "
            f"Tabla={table_name or 'desconocida'}: {reason}"
        ),
        internal_code=DEFENSIVE_TENANT_FILTER_REQUIRED,
    )


def apply_tenant_filter(
    query: ClauseElement,
    client_id: Optional[Union[int, UUID]] = None,
    table_name: Optional[str] = None,
    tenant_column: str = "cliente_id",
    identity_scope: Optional[IdentityScope] = None,
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
        SecurityError: Dedicated path sin filter aplicable (TD-08)
    """
    if identity_scope == IdentityScope.ENGINE_SCOPED:
        logger.debug(
            "[TENANT_FILTER] ENGINE_SCOPED identity — omitiendo filtro tenant"
        )
        return query

    # ✅ CORRECCIÓN: Obtener nombre de tabla PRIMERO para verificar si es global
    # Si es tabla global, no necesita client_id ni filtro de tenant
    if table_name is None:
        table_name = get_table_name_from_query(query)
    
    base_tables = collect_base_table_names_from_query(query)
    if base_tables and _all_tables_are_global(base_tables):
        logger.debug(
            "[TENANT_FILTER] JOIN/SELECT catálogo global %s — omitiendo filtro",
            sorted(base_tables),
        )
        return query

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
        if _is_dedicated_tenant_context() and _select_has_explicit_tenant_predicate(
            query, tenant_column
        ):
            logger.debug(
                "[TENANT_FILTER] TD-08 satisfied — predicado tenant explícito "
                f"(table={table_name})"
            )
            return query

        # Obtener tabla de la query
        froms = (
            query.get_final_froms()
            if hasattr(query, "get_final_froms")
            else query.froms
        )
        from_clause = froms[0] if froms else None
        if from_clause is None:
            if _is_dedicated_tenant_context():
                _raise_defensive_tenant_filter_required(
                    table_name, "Select sin FROM identificable"
                )
            return query

        # Verificar si ya tiene filtro de tenant
        # (simplificado: asumimos que no lo tiene y lo agregamos)
        tenant_col = getattr(from_clause.c, tenant_column, None)
        if tenant_col is not None:
            if _is_dedicated_tenant_context():
                logger.debug(
                    f"[TENANT_FILTER] TD-08 defensive filter applied "
                    f"(dedicated, table={table_name})"
                )
            # Agregar condición WHERE
            if query.whereclause is None:
                query = query.where(tenant_col == client_id)
            else:
                query = query.where(and_(query.whereclause, tenant_col == client_id))
        elif _is_dedicated_tenant_context():
            _raise_defensive_tenant_filter_required(
                table_name,
                f"columna {tenant_column} no disponible en la tabla",
            )

    elif isinstance(query, (Update, Delete)):
        # Para Update/Delete, agregar condición WHERE
        from_clause = query.table if hasattr(query, 'table') else None
        if from_clause is None:
            if _is_dedicated_tenant_context():
                _raise_defensive_tenant_filter_required(
                    table_name, "Update/Delete sin tabla identificable"
                )
            return query

        tenant_col = getattr(from_clause.c, tenant_column, None)
        if tenant_col is not None:
            if _is_dedicated_tenant_context():
                logger.debug(
                    f"[TENANT_FILTER] TD-08 defensive filter applied "
                    f"(dedicated, table={table_name})"
                )
            if query.whereclause is None:
                query = query.where(tenant_col == client_id)
            else:
                query = query.where(and_(query.whereclause, tenant_col == client_id))
        elif _is_dedicated_tenant_context():
            _raise_defensive_tenant_filter_required(
                table_name,
                f"columna {tenant_column} no disponible en la tabla",
            )
    
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
            froms = (
                query.get_final_froms()
                if hasattr(query, "get_final_froms")
                else query.froms
            )
            if froms:
                name = _first_base_table_name(froms[0])
                if name:
                    return name
        elif isinstance(query, (Update, Delete)):
            if hasattr(query, 'table'):
                name = _first_base_table_name(query.table)
                if name:
                    return name
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


def _extract_text_clause_bind_params(query: TextClause) -> dict[str, Any]:
    """
    Extrae valores de bind parameters de un TextClause (SQLAlchemy 1.x y 2.x).

    En SA2, ``query.bindparams`` es callable; los valores están en ``compile().params``
    o en ``query._bindparams`` (BindParameter con .value).
    """
    params: dict[str, Any] = {}

    try:
        compiled = query.compile()
        if hasattr(compiled, "params") and compiled.params:
            return dict(compiled.params)
    except Exception:
        pass

    bindparams_map = getattr(query, "_bindparams", None)
    if bindparams_map:
        for key, bind in bindparams_map.items():
            params[key] = bind.value if hasattr(bind, "value") else bind
        if params:
            return params

    bp = getattr(query, "bindparams", None)
    if bp is not None and not callable(bp) and hasattr(bp, "keys"):
        try:
            for key in bp.keys():
                val = bp[key]
                params[key] = getattr(val, "value", val)
        except Exception:
            pass

    return params


def apply_tenant_filter_to_text_clause(
    query: TextClause,
    client_id: Optional[Union[int, UUID]] = None,
    table_name: Optional[str] = None,
    tenant_column: str = "cliente_id",
    identity_scope: Optional[IdentityScope] = None,
) -> TextClause:
    """
    Aplica filtro de tenant automáticamente a TextClause.
    
    ✅ FASE 1 SEGURIDAD: Protege queries TextClause contra fuga de datos entre tenants.
    
    Intenta parsear el SQL y agregar filtro de cliente_id si no existe.
    Si la query ya tiene filtro de tenant, no la modifica.
    Si es una tabla global, no aplica filtro.
    
    Args:
        query: TextClause a modificar
        client_id: ID del cliente (opcional, usa contexto si no se proporciona)
        table_name: Nombre de la tabla (opcional, se infiere si es posible)
        tenant_column: Nombre de la columna de tenant (default: "cliente_id")
    
    Returns:
        TextClause modificado con filtro de tenant (o original si no se puede modificar)
    
    Raises:
        ValidationError: Si no hay contexto ni client_id y bypass no está permitido
        SecurityError: Dedicated path sin filter aplicable (TD-08)

    Example:
        from sqlalchemy import text
        
        # Query sin filtro de tenant
        query = text("SELECT * FROM usuario WHERE es_activo = 1").bindparams()
        
        # Aplicar filtro automático
        query_protegida = apply_tenant_filter_to_text_clause(query, client_id=cliente_id)
        # Resultado: "SELECT * FROM usuario WHERE es_activo = 1 AND cliente_id = :cliente_id"
    """
    if identity_scope == IdentityScope.ENGINE_SCOPED:
        logger.debug(
            "[TENANT_FILTER] ENGINE_SCOPED identity TextClause — omitiendo filtro tenant"
        )
        return query

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
    try:
        # TextClause tiene un atributo text que contiene el SQL original
        query_str = query.text if hasattr(query, 'text') else str(query)
    except Exception:
        query_str = str(query)
    
    query_lower = query_str.lower()
    
    # INSERT no lleva WHERE; el cliente_id ya va en VALUES. No aplicar filtro automático.
    if query_lower.strip().startswith("insert"):
        logger.debug("[TENANT_FILTER] INSERT detectado, omitiendo filtro (valores explícitos)")
        return query
    
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
    try:
        modified_query_str = _add_tenant_filter_to_sql(
            query_str, 
            tenant_column, 
            client_id
        )
        
        existing_params = _extract_text_clause_bind_params(query)
        existing_params[tenant_column] = client_id
        
        # Crear nuevo TextClause con filtro agregado
        new_query = text(modified_query_str).bindparams(**existing_params)

        if _is_dedicated_tenant_context():
            if not _has_tenant_filter(modified_query_str, tenant_column, client_id):
                _raise_defensive_tenant_filter_required(
                    table_name, "no se pudo inyectar filtro SQL en TextClause"
                )
            logger.debug(
                f"[TENANT_FILTER] TD-08 defensive filter applied "
                f"(dedicated TextClause, table={table_name})"
            )
        else:
            logger.debug(
                f"[TENANT_FILTER] Filtro de tenant agregado automáticamente a TextClause. "
                f"Tabla: {table_name}"
            )

        return new_query
    except SecurityError:
        raise
    except Exception as e:
        if _is_dedicated_tenant_context():
            _raise_defensive_tenant_filter_required(table_name, str(e))
        logger.warning(
            f"[TENANT_FILTER] No se pudo aplicar filtro automático a TextClause: {e}. "
            f"Query: {query_str[:200]}..."
        )
        return query


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


def qmark_sql_text(
    sql: str,
    params: Optional[Union[tuple, list]] = None,
) -> TextClause:
    """
    Convierte SQL legacy con placeholders ``?`` a ``TextClause`` (F12-E2B3K).

    Equivalente al branch string de ``execute_query`` sin emitir ``[QUERY] DEPRECATED``.
    """
    if not params:
        return text(sql)
    seq = list(params)
    if not seq:
        return text(sql)
    names = [f"p{i}" for i in range(len(seq))]
    query_text = sql
    for i, name in enumerate(names):
        query_text = query_text.replace("?", f":{name}", 1)
    return text(query_text).bindparams(**dict(zip(names, seq)))
