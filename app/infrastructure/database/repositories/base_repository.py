# app/infrastructure/database/repositories/base_repository.py
"""
BaseRepository: Clase base abstracta para todos los repositorios.

✅ FASE 3: ARQUITECTURA - Completar capa de repositorios
- Abstrae el acceso a datos
- Maneja multi-tenancy automáticamente
- Proporciona operaciones CRUD estándar
- Facilita testing y cambio de BD
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TypeVar, Generic
import logging

# ✅ COMPATIBILIDAD: Re-exportar BaseService desde su nueva ubicación
# BaseService ahora está en app/core/application/base_service.py (corrige violación de capas)
from app.core.application.base_service import BaseService

from app.infrastructure.database.queries import (
    execute_query,
    execute_insert,
    execute_update,
    execute_procedure
)
from app.infrastructure.database.connection import DatabaseConnection
from app.core.exceptions import DatabaseError, NotFoundError, ValidationError
from app.core.tenant.context import get_current_client_id
from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Clase base abstracta para todos los repositorios.
    
    Proporciona operaciones CRUD estándar y manejo automático de multi-tenancy.
    Cada módulo debe crear su propio repositorio que herede de esta clase.
    
    Ejemplo de uso:
    ```python
    class UsuarioRepository(BaseRepository[Usuario]):
        def __init__(self):
            super().__init__(
                table_name="usuario",
                id_column="usuario_id",
                tenant_column="cliente_id"
            )
    ```
    """
    
    def __init__(
        self,
        table_name: str,
        id_column: str = "id",
        tenant_column: Optional[str] = "cliente_id",
        connection_type: DatabaseConnection = DatabaseConnection.DEFAULT
    ):
        """
        Inicializa el repositorio base.
        
        Args:
            table_name: Nombre de la tabla en la BD
            id_column: Nombre de la columna de ID primario
            tenant_column: Nombre de la columna de tenant (None si no aplica)
            connection_type: Tipo de conexión (DEFAULT o ADMIN)
        """
        self.table_name = table_name
        self.id_column = id_column
        self.tenant_column = tenant_column
        self.connection_type = connection_type
    
    def _get_current_client_id(self) -> Optional[int]:
        """Obtiene el cliente_id del contexto actual."""
        try:
            return get_current_client_id()
        except RuntimeError:
            # Sin contexto (scripts de fondo, etc.)
            return None
    
    def _build_tenant_filter(
        self, 
        client_id: Optional[int] = None,
        allow_no_context: bool = False
    ) -> tuple:
        """
        Construye el filtro de tenant para queries.
        
        ✅ CORRECCIÓN AUDITORÍA: Filtro OBLIGATORIO por defecto.
        El filtro cliente_id se aplica SIEMPRE excepto en casos muy específicos.
        
        Args:
            client_id: ID del cliente (opcional, usa contexto si no se proporciona)
            allow_no_context: Si True, permite queries sin contexto (solo si ALLOW_TENANT_FILTER_BYPASS=True)
        
        Returns:
            Tuple (where_clause, params) para agregar a queries
        
        Raises:
            ValidationError: Si no hay contexto ni client_id y bypass no está permitido
        """
        if not self.tenant_column:
            # Tabla sin columna de tenant (tabla global)
            return ("", ())
        
        target_client_id = client_id or self._get_current_client_id()
        
        if target_client_id is None:
            # ✅ CORRECCIÓN AUDITORÍA: Bypass solo si está habilitado en configuración
            if allow_no_context and settings.ALLOW_TENANT_FILTER_BYPASS:
                # ⚠️ BYPASS PERMITIDO: Solo si está habilitado globalmente Y se solicita explícitamente
                logger.error(
                    f"[SECURITY CRITICAL] Query sin filtro de tenant permitida para tabla {self.table_name}. "
                    f"Esto es un BYPASS de seguridad y solo debería usarse en scripts de migración o mantenimiento. "
                    f"Si ves este mensaje en producción, revisa inmediatamente."
                )
                return ("", ())
            elif allow_no_context and not settings.ALLOW_TENANT_FILTER_BYPASS:
                # ⚠️ BYPASS SOLICITADO PERO NO PERMITIDO: Rechazar
                logger.error(
                    f"[SECURITY] Intento de bypass de filtro de tenant rechazado para tabla {self.table_name}. "
                    f"ALLOW_TENANT_FILTER_BYPASS está desactivado. "
                    f"Proporcione client_id explícitamente."
                )
                raise ValidationError(
                    detail=(
                        f"Bypass de filtro de tenant no permitido para {self.table_name}. "
                        f"El filtro cliente_id es OBLIGATORIO por seguridad. "
                        f"Proporcione client_id explícitamente. "
                        f"Si es un script de migración, active ALLOW_TENANT_FILTER_BYPASS temporalmente."
                    ),
                    internal_code="TENANT_FILTER_BYPASS_DISABLED"
                )
            else:
                # ✅ SEGURIDAD: Requerir contexto de tenant o client_id explícito
                raise ValidationError(
                    detail=(
                        f"Contexto de tenant OBLIGATORIO para acceder a {self.table_name}. "
                        f"Proporcione client_id explícitamente. "
                        f"El filtro cliente_id es requerido por seguridad multi-tenant."
                    ),
                    internal_code="TENANT_CONTEXT_REQUIRED"
                )
        
        # ✅ FILTRO OBLIGATORIO: Siempre aplicar filtro de tenant
        return (f"AND {self.tenant_column} = ?", (target_client_id,))
    
    def find_by_id(
        self,
        entity_id: Any,
        client_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca una entidad por su ID.
        
        Args:
            entity_id: ID de la entidad
            client_id: ID del cliente (opcional, usa contexto si no se proporciona)
        
        Returns:
            Diccionario con los datos de la entidad o None si no existe
        """
        tenant_filter, tenant_params = self._build_tenant_filter(client_id)
        
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE {self.id_column} = ?
            {tenant_filter}
        """
        params = (entity_id,) + tenant_params
        
        try:
            results = execute_query(
                query,
                params,
                connection_type=self.connection_type,
                client_id=client_id
            )
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error en find_by_id para {self.table_name}: {str(e)}")
            raise DatabaseError(
                detail=f"Error al buscar {self.table_name} por ID: {str(e)}",
                internal_code="REPOSITORY_FIND_ERROR"
            )
    
    def find_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        client_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca todas las entidades que cumplan con los filtros.
        
        Args:
            filters: Diccionario con filtros {campo: valor}
            client_id: ID del cliente (opcional)
            limit: Límite de resultados
            offset: Offset para paginación
            order_by: Campo para ordenar (ej: "nombre ASC")
        
        Returns:
            Lista de diccionarios con los resultados
        """
        tenant_filter, tenant_params = self._build_tenant_filter(client_id)
        
        where_clauses = []
        params = []
        
        # Agregar filtros personalizados
        if filters:
            for field, value in filters.items():
                if value is not None:
                    where_clauses.append(f"{field} = ?")
                    params.append(value)
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        where_clause += tenant_filter
        params.extend(tenant_params)
        
        # Construir query
        query = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" OFFSET {offset or 0} ROWS FETCH NEXT {limit} ROWS ONLY"
        
        try:
            return execute_query(
                query,
                tuple(params),
                connection_type=self.connection_type,
                client_id=client_id
            )
        except Exception as e:
            logger.error(f"Error en find_all para {self.table_name}: {str(e)}")
            raise DatabaseError(
                detail=f"Error al buscar {self.table_name}: {str(e)}",
                internal_code="REPOSITORY_FIND_ALL_ERROR"
            )
    
    def create(
        self,
        data: Dict[str, Any],
        client_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Crea una nueva entidad.
        
        Args:
            data: Diccionario con los datos de la entidad
            client_id: ID del cliente (opcional, usa contexto si no se proporciona)
        
        Returns:
            Diccionario con los datos de la entidad creada (incluyendo ID generado)
        """
        # Agregar cliente_id automáticamente si aplica
        if self.tenant_column and self.tenant_column not in data:
            target_client_id = client_id or self._get_current_client_id()
            if target_client_id:
                data[self.tenant_column] = target_client_id
            else:
                # ✅ SEGURIDAD: Requerir contexto de tenant o client_id explícito para crear
                raise ValidationError(
                    detail=(
                        f"Contexto de tenant requerido para crear en {self.table_name}. "
                        f"Proporcione client_id explícitamente."
                    ),
                    internal_code="TENANT_CONTEXT_REQUIRED_FOR_CREATE"
                )
        
        # Construir query INSERT
        columns = list(data.keys())
        placeholders = ", ".join(["?" for _ in columns])
        columns_str = ", ".join(columns)
        values = tuple(data.values())
        
        query = f"""
            INSERT INTO {self.table_name} ({columns_str})
            OUTPUT INSERTED.*
            VALUES ({placeholders})
        """
        
        try:
            result = execute_insert(
                query,
                values,
                connection_type=self.connection_type,
                client_id=client_id
            )
            return result[0] if result else data
        except Exception as e:
            logger.error(f"Error en create para {self.table_name}: {str(e)}")
            raise DatabaseError(
                detail=f"Error al crear {self.table_name}: {str(e)}",
                internal_code="REPOSITORY_CREATE_ERROR"
            )
    
    def update(
        self,
        entity_id: Any,
        data: Dict[str, Any],
        client_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Actualiza una entidad existente.
        
        Args:
            entity_id: ID de la entidad a actualizar
            data: Diccionario con los campos a actualizar
            client_id: ID del cliente (opcional, para validación)
        
        Returns:
            Diccionario con los datos actualizados
        
        Raises:
            NotFoundError: Si la entidad no existe
        """
        # Verificar que existe
        existing = self.find_by_id(entity_id, client_id)
        if not existing:
            raise NotFoundError(
                detail=f"{self.table_name} con ID {entity_id} no encontrado",
                internal_code="ENTITY_NOT_FOUND"
            )
        
        # Construir query UPDATE
        set_clauses = [f"{key} = ?" for key in data.keys()]
        set_clause = ", ".join(set_clauses)
        values = tuple(data.values())
        
        tenant_filter, tenant_params = self._build_tenant_filter(client_id)
        
        query = f"""
            UPDATE {self.table_name}
            SET {set_clause}
            OUTPUT INSERTED.*
            WHERE {self.id_column} = ?
            {tenant_filter}
        """
        params = values + (entity_id,) + tenant_params
        
        try:
            result = execute_update(
                query,
                params,
                connection_type=self.connection_type,
                client_id=client_id
            )
            return result[0] if result else existing
        except Exception as e:
            logger.error(f"Error en update para {self.table_name}: {str(e)}")
            raise DatabaseError(
                detail=f"Error al actualizar {self.table_name}: {str(e)}",
                internal_code="REPOSITORY_UPDATE_ERROR"
            )
    
    def delete(
        self,
        entity_id: Any,
        client_id: Optional[int] = None,
        soft_delete: bool = True,
        soft_delete_column: str = "es_activo"
    ) -> bool:
        """
        Elimina una entidad (soft delete por defecto).
        
        Args:
            entity_id: ID de la entidad a eliminar
            client_id: ID del cliente (opcional, para validación)
            soft_delete: Si True, hace soft delete (marca como inactivo)
            soft_delete_column: Nombre de la columna para soft delete
        
        Returns:
            True si se eliminó correctamente
        
        Raises:
            NotFoundError: Si la entidad no existe
        """
        # Verificar que existe
        existing = self.find_by_id(entity_id, client_id)
        if not existing:
            raise NotFoundError(
                detail=f"{self.table_name} con ID {entity_id} no encontrado",
                internal_code="ENTITY_NOT_FOUND"
            )
        
        tenant_filter, tenant_params = self._build_tenant_filter(client_id)
        
        if soft_delete:
            # Soft delete: marcar como inactivo
            query = f"""
                UPDATE {self.table_name}
                SET {soft_delete_column} = 0
                WHERE {self.id_column} = ?
                {tenant_filter}
            """
            params = (entity_id,) + tenant_params
        else:
            # Hard delete: eliminar físicamente
            query = f"""
                DELETE FROM {self.table_name}
                WHERE {self.id_column} = ?
                {tenant_filter}
            """
            params = (entity_id,) + tenant_params
        
        try:
            execute_update(
                query,
                params,
                connection_type=self.connection_type,
                client_id=client_id
            )
            return True
        except Exception as e:
            logger.error(f"Error en delete para {self.table_name}: {str(e)}")
            raise DatabaseError(
                detail=f"Error al eliminar {self.table_name}: {str(e)}",
                internal_code="REPOSITORY_DELETE_ERROR"
            )
    
    def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
        client_id: Optional[int] = None
    ) -> int:
        """
        Cuenta el número de entidades que cumplan con los filtros.
        
        Args:
            filters: Diccionario con filtros {campo: valor}
            client_id: ID del cliente (opcional)
        
        Returns:
            Número de entidades
        """
        tenant_filter, tenant_params = self._build_tenant_filter(client_id)
        
        where_clauses = []
        params = []
        
        if filters:
            for field, value in filters.items():
                if value is not None:
                    where_clauses.append(f"{field} = ?")
                    params.append(value)
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        where_clause += tenant_filter
        params.extend(tenant_params)
        
        query = f"SELECT COUNT(*) as total FROM {self.table_name} WHERE {where_clause}"
        
        try:
            result = execute_query(
                query,
                tuple(params),
                connection_type=self.connection_type,
                client_id=client_id
            )
            return result[0]["total"] if result else 0
        except Exception as e:
            logger.error(f"Error en count para {self.table_name}: {str(e)}")
            raise DatabaseError(
                detail=f"Error al contar {self.table_name}: {str(e)}",
                internal_code="REPOSITORY_COUNT_ERROR"
            )
    
    def exists(
        self,
        entity_id: Any,
        client_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si una entidad existe.
        
        Args:
            entity_id: ID de la entidad
            client_id: ID del cliente (opcional)
        
        Returns:
            True si existe, False en caso contrario
        """
        return self.find_by_id(entity_id, client_id) is not None
