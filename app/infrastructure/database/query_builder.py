# app/infrastructure/database/query_builder.py
"""
Helper para construir queries SQL de forma segura.

✅ SEGURIDAD: Previene SQL injection mediante:
- Validación de nombres de campos (solo alfanuméricos y _)
- Uso obligatorio de parámetros para valores
- Whitelist de operadores permitidos
- Construcción segura de WHERE clauses

Ejemplo de uso:
    from app.infrastructure.database.query_builder import SafeQueryBuilder
    
    filters = {"nombre": "Juan", "edad": 25}
    where_clause, params = SafeQueryBuilder.build_where_clause(filters)
    query = f"SELECT * FROM usuarios WHERE {where_clause}"
    results = execute_query(query, params)
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class SafeQueryBuilder:
    """
    Helper para construir queries SQL de forma segura.
    
    Previene SQL injection mediante validación estricta de campos
    y uso obligatorio de parámetros para valores.
    """
    
    # Operadores permitidos en WHERE clauses
    ALLOWED_OPERATORS = ["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN", "IS NULL", "IS NOT NULL"]
    
    # Funciones SQL permitidas (para validación futura)
    ALLOWED_FUNCTIONS = ["LOWER", "UPPER", "COUNT", "MAX", "MIN", "SUM", "AVG"]
    
    # Patrón para validar nombres de campos (solo alfanuméricos, _ y . para tablas.campos)
    FIELD_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_.]*$')
    
    @staticmethod
    def validate_field_name(field: str) -> bool:
        """
        Valida que un nombre de campo sea seguro.
        
        Args:
            field: Nombre del campo a validar
        
        Returns:
            True si es válido, False en caso contrario
        
        Raises:
            ValueError: Si el campo contiene caracteres peligrosos
        """
        if not field:
            raise ValueError("Nombre de campo no puede estar vacío")
        
        if not SafeQueryBuilder.FIELD_PATTERN.match(field):
            raise ValueError(
                f"Nombre de campo inválido: '{field}'. "
                f"Solo se permiten letras, números, guiones bajos y puntos."
            )
        
        # Prevenir SQL injection mediante palabras clave peligrosas
        dangerous_keywords = [
            "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE",
            "EXEC", "EXECUTE", "UNION", "SELECT", "FROM", "WHERE"
        ]
        
        field_upper = field.upper()
        for keyword in dangerous_keywords:
            if keyword in field_upper:
                raise ValueError(
                    f"Nombre de campo contiene palabra clave peligrosa: '{field}'. "
                    f"Esto podría ser un intento de SQL injection."
                )
        
        return True
    
    @staticmethod
    def build_where_clause(
        filters: Dict[str, Any],
        operator: str = "=",
        allow_null: bool = True
    ) -> Tuple[str, Tuple]:
        """
        Construye una cláusula WHERE de forma segura.
        
        Args:
            filters: Diccionario con filtros {campo: valor}
            operator: Operador a usar (=, !=, >, <, >=, <=, LIKE, IN)
            allow_null: Si True, permite valores None (se omiten del filtro)
        
        Returns:
            Tuple (where_clause, params) donde:
            - where_clause: String con la cláusula WHERE (ej: "campo1 = ? AND campo2 = ?")
            - params: Tupla con los valores para los parámetros
        
        Raises:
            ValueError: Si el operador no está permitido o el campo es inválido
        
        Ejemplo:
            filters = {"nombre": "Juan", "edad": 25}
            where_clause, params = SafeQueryBuilder.build_where_clause(filters)
            # where_clause = "nombre = ? AND edad = ?"
            # params = ("Juan", 25)
        """
        if operator not in SafeQueryBuilder.ALLOWED_OPERATORS:
            raise ValueError(
                f"Operador '{operator}' no permitido. "
                f"Operadores permitidos: {', '.join(SafeQueryBuilder.ALLOWED_OPERATORS)}"
            )
        
        where_clauses = []
        params = []
        
        for field, value in filters.items():
            # Validar nombre de campo
            SafeQueryBuilder.validate_field_name(field)
            
            # Omitir valores None si allow_null es True
            if allow_null and value is None:
                continue
            
            # Construir cláusula según el operador
            if operator.upper() == "LIKE":
                where_clauses.append(f"{field} LIKE ?")
                # Agregar wildcards si no están presentes
                if isinstance(value, str) and "%" not in value:
                    params.append(f"%{value}%")
                else:
                    params.append(value)
            
            elif operator.upper() == "IN":
                if not isinstance(value, (list, tuple)):
                    raise ValueError(f"Operador IN requiere una lista o tupla, recibido: {type(value)}")
                
                if not value:  # Lista vacía
                    continue
                
                placeholders = ", ".join(["?" for _ in value])
                where_clauses.append(f"{field} IN ({placeholders})")
                params.extend(value)
            
            elif operator.upper() in ["IS NULL", "IS NOT NULL"]:
                # IS NULL e IS NOT NULL no requieren parámetros
                where_clauses.append(f"{field} {operator.upper()}")
            
            else:
                # Operadores estándar (=, !=, >, <, >=, <=)
                where_clauses.append(f"{field} {operator} ?")
                params.append(value)
        
        if not where_clauses:
            return "1=1", ()  # Sin filtros, retornar condición siempre verdadera
        
        where_clause = " AND ".join(where_clauses)
        return where_clause, tuple(params)
    
    @staticmethod
    def build_order_by(
        order_fields: List[str],
        valid_fields: Optional[List[str]] = None,
        default_order: str = "ASC"
    ) -> str:
        """
        Construye una cláusula ORDER BY de forma segura.
        
        Args:
            order_fields: Lista de campos para ordenar (ej: ["nombre", "edad DESC"])
            valid_fields: Lista de campos válidos (whitelist). Si None, valida formato
            default_order: Orden por defecto si no se especifica (ASC o DESC)
        
        Returns:
            String con la cláusula ORDER BY (ej: "nombre ASC, edad DESC")
        
        Raises:
            ValueError: Si algún campo no está en la whitelist o tiene formato inválido
        
        Ejemplo:
            order_by = SafeQueryBuilder.build_order_by(
                ["nombre", "edad DESC"],
                valid_fields=["nombre", "edad", "fecha_creacion"]
            )
            # Resultado: "nombre ASC, edad DESC"
        """
        if not order_fields:
            return ""
        
        order_clauses = []
        
        for field_spec in order_fields:
            # Separar campo y dirección
            parts = field_spec.strip().split()
            field = parts[0]
            direction = parts[1].upper() if len(parts) > 1 else default_order.upper()
            
            # Validar dirección
            if direction not in ["ASC", "DESC"]:
                direction = default_order.upper()
            
            # Validar nombre de campo
            SafeQueryBuilder.validate_field_name(field)
            
            # Si hay whitelist, validar contra ella
            if valid_fields is not None:
                if field not in valid_fields:
                    raise ValueError(
                        f"Campo '{field}' no está en la lista de campos válidos. "
                        f"Campos permitidos: {', '.join(valid_fields)}"
                    )
            
            order_clauses.append(f"{field} {direction}")
        
        return ", ".join(order_clauses)
    
    @staticmethod
    def build_pagination(
        offset: int = 0,
        limit: Optional[int] = None
    ) -> Tuple[str, Tuple]:
        """
        Construye cláusula de paginación para SQL Server.
        
        Args:
            offset: Número de registros a saltar
            limit: Número máximo de registros a retornar
        
        Returns:
            Tuple (pagination_clause, params)
        
        Ejemplo:
            pagination, params = SafeQueryBuilder.build_pagination(offset=10, limit=20)
            # Resultado: "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            # params = (10, 20)
        """
        if limit is None:
            return "", ()
        
        if offset < 0:
            offset = 0
        if limit < 1:
            limit = 1
        
        return "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY", (offset, limit)


# Función de conveniencia para uso rápido
def build_safe_where(filters: Dict[str, Any], operator: str = "=") -> Tuple[str, Tuple]:
    """
    Función de conveniencia para construir WHERE clause de forma segura.
    
    Ejemplo:
        where_clause, params = build_safe_where({"nombre": "Juan", "edad": 25})
    """
    return SafeQueryBuilder.build_where_clause(filters, operator)


# Exportar para uso fácil
__all__ = ["SafeQueryBuilder", "build_safe_where"]


