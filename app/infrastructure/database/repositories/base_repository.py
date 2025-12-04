# app/infrastructure/database/repositories/base_repository.py
"""
BaseRepository: Clase base abstracta para todos los repositorios.

✅ FASE 2: Refactorizado para usar conexiones async
- Todas las operaciones son async
- Usa SQLAlchemy AsyncSession
- Maneja multi-tenancy automáticamente
- Proporciona operaciones CRUD estándar
- Facilita testing y cambio de BD
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TypeVar, Generic
from uuid import UUID
import logging

# ✅ COMPATIBILIDAD: Re-exportar BaseService desde su nueva ubicación
# BaseService ahora está en app/core/application/base_service.py (corrige violación de capas)
from app.core.application.base_service import BaseService

# ✅ FASE 2: Importar funciones async
from app.infrastructure.database.queries_async import (
    execute_query,
    execute_insert,
    execute_update,
)
from app.infrastructure.database.connection_async import DatabaseConnection, get_db_connection
from app.core.exceptions import DatabaseError, NotFoundError, ValidationError
from app.core.tenant.context import get_current_client_id
from app.core.config import settings
from sqlalchemy import select, update, delete, insert, and_
from sqlalchemy.sql import Select, Update, Delete, Insert
from sqlalchemy.ext.asyncio import AsyncSession

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
    
    def _get_current_client_id(self) -> Optional[UUID]:
        """Obtiene el cliente_id del contexto actual (UUID)."""
        try:
            return get_current_client_id()
        except RuntimeError:
            # Sin contexto (scripts de fondo, etc.)
            return None
    
    def _build_tenant_filter(
        self, 
        client_id: Optional[UUID] = None,
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
        
        # ⚠️ NOTA: Este método ya no se usa en los métodos actuales que usan SQLAlchemy Core
        # Se mantiene para compatibilidad con código legacy que pueda usarlo
        # El filtro de tenant ahora se aplica directamente en las queries SQLAlchemy
        return (f"AND {self.tenant_column} = ?", (target_client_id,))
    
    async def find_by_id(
        self,
        entity_id: Any,  # UUID o str
        client_id: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca una entidad por su ID.
        
        ✅ FASE 2: Refactorizado para usar async.
        
        Args:
            entity_id: ID de la entidad
            client_id: ID del cliente (opcional, usa contexto si no se proporciona)
        
        Returns:
            Diccionario con los datos de la entidad o None si no existe
        """
        # ✅ FASE 2: Usar SQLAlchemy Core con async
        from app.infrastructure.database.tables import metadata
        from sqlalchemy import select
        
        table = metadata.tables.get(self.table_name)
        if not table:
            raise DatabaseError(
                detail=f"Tabla {self.table_name} no encontrada en metadata",
                internal_code="TABLE_NOT_FOUND"
            )
        
        query = select(table).where(table.c[self.id_column] == entity_id)
        
        # Aplicar filtro de tenant
        if self.tenant_column:
            target_client_id = client_id or self._get_current_client_id()
            if target_client_id:
                query = query.where(table.c[self.tenant_column] == target_client_id)
        
        try:
            results = await execute_query(
                query,
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
    
    async def find_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        client_id: Optional[UUID] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca todas las entidades que cumplan con los filtros.
        
        ✅ FASE 2: Refactorizado para usar async.
        
        Args:
            filters: Diccionario con filtros {campo: valor}
            client_id: ID del cliente (opcional)
            limit: Límite de resultados
            offset: Offset para paginación
            order_by: Campo para ordenar (ej: "nombre ASC")
        
        Returns:
            Lista de diccionarios con los resultados
        """
        # ✅ FASE 2: Usar SQLAlchemy Core con async
        from app.infrastructure.database.tables import metadata
        from sqlalchemy import select
        
        table = metadata.tables.get(self.table_name)
        if not table:
            raise DatabaseError(
                detail=f"Tabla {self.table_name} no encontrada en metadata",
                internal_code="TABLE_NOT_FOUND"
            )
        
        query = select(table)
        
        # Aplicar filtros personalizados
        if filters:
            for field, value in filters.items():
                if value is not None and field in table.c:
                    query = query.where(table.c[field] == value)
        
        # Aplicar filtro de tenant
        if self.tenant_column:
            target_client_id = client_id or self._get_current_client_id()
            if target_client_id:
                query = query.where(table.c[self.tenant_column] == target_client_id)
        
        # Aplicar ordenamiento
        if order_by:
            parts = order_by.split()
            if len(parts) == 2:
                field, direction = parts
                if field in table.c:
                    if direction.upper() == "DESC":
                        query = query.order_by(table.c[field].desc())
                    else:
                        query = query.order_by(table.c[field])
        
        # Aplicar paginación
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        try:
            return await execute_query(
                query,
                connection_type=self.connection_type,
                client_id=client_id
            )
        except Exception as e:
            logger.error(f"Error en find_all para {self.table_name}: {str(e)}")
            raise DatabaseError(
                detail=f"Error al buscar {self.table_name}: {str(e)}",
                internal_code="REPOSITORY_FIND_ALL_ERROR"
            )
    
    async def create(
        self,
        data: Dict[str, Any],
        client_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Crea una nueva entidad.
        
        ✅ FASE 2: Refactorizado para usar async.
        
        Args:
            data: Diccionario con los datos de la entidad
            client_id: ID del cliente (opcional, usa contexto si no se proporciona)
        
        Returns:
            Diccionario con los datos de la entidad creada (incluyendo ID generado)
        """
        # ✅ FASE 2: Usar SQLAlchemy Core con async
        from app.infrastructure.database.tables import metadata
        from sqlalchemy import insert
        
        table = metadata.tables.get(self.table_name)
        if not table:
            raise DatabaseError(
                detail=f"Tabla {self.table_name} no encontrada en metadata",
                internal_code="TABLE_NOT_FOUND"
            )
        
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
        query = insert(table).values(**data)
        
        try:
            result = await execute_insert(
                query,
                connection_type=self.connection_type,
                client_id=client_id
            )
            return result if result else data
        except Exception as e:
            logger.error(f"Error en create para {self.table_name}: {str(e)}")
            raise DatabaseError(
                detail=f"Error al crear {self.table_name}: {str(e)}",
                internal_code="REPOSITORY_CREATE_ERROR"
            )
    
    async def update(
        self,
        entity_id: Any,  # UUID o str
        data: Dict[str, Any],
        client_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Actualiza una entidad existente.
        
        ✅ FASE 2: Refactorizado para usar async.
        
        Args:
            entity_id: ID de la entidad a actualizar
            data: Diccionario con los campos a actualizar
            client_id: ID del cliente (opcional, para validación)
        
        Returns:
            Diccionario con los datos actualizados
        
        Raises:
            NotFoundError: Si la entidad no existe
        """
        # ✅ FASE 2: Usar SQLAlchemy Core con async
        from app.infrastructure.database.tables import metadata
        from sqlalchemy import update
        
        table = metadata.tables.get(self.table_name)
        if not table:
            raise DatabaseError(
                detail=f"Tabla {self.table_name} no encontrada en metadata",
                internal_code="TABLE_NOT_FOUND"
            )
        
        # Verificar que existe
        existing = await self.find_by_id(entity_id, client_id)
        if not existing:
            raise NotFoundError(
                detail=f"{self.table_name} con ID {entity_id} no encontrado",
                internal_code="ENTITY_NOT_FOUND"
            )
        
        # Construir query UPDATE
        query = update(table).where(table.c[self.id_column] == entity_id).values(**data)
        
        # Aplicar filtro de tenant
        if self.tenant_column:
            target_client_id = client_id or self._get_current_client_id()
            if target_client_id:
                query = query.where(table.c[self.tenant_column] == target_client_id)
        
        try:
            result = await execute_update(
                query,
                connection_type=self.connection_type,
                client_id=client_id
            )
            return result if result else existing
        except Exception as e:
            logger.error(f"Error en update para {self.table_name}: {str(e)}")
            raise DatabaseError(
                detail=f"Error al actualizar {self.table_name}: {str(e)}",
                internal_code="REPOSITORY_UPDATE_ERROR"
            )
    
    async def delete(
        self,
        entity_id: Any,  # UUID o str
        client_id: Optional[UUID] = None,
        soft_delete: bool = True,
        soft_delete_column: str = "es_activo"
    ) -> bool:
        """
        Elimina una entidad (soft delete por defecto).
        
        ✅ FASE 2: Refactorizado para usar async.
        
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
        # ✅ FASE 2: Usar SQLAlchemy Core con async
        from app.infrastructure.database.tables import metadata
        from sqlalchemy import update, delete
        
        table = metadata.tables.get(self.table_name)
        if not table:
            raise DatabaseError(
                detail=f"Tabla {self.table_name} no encontrada en metadata",
                internal_code="TABLE_NOT_FOUND"
            )
        
        # Verificar que existe
        existing = await self.find_by_id(entity_id, client_id)
        if not existing:
            raise NotFoundError(
                detail=f"{self.table_name} con ID {entity_id} no encontrado",
                internal_code="ENTITY_NOT_FOUND"
            )
        
        # Aplicar filtro de tenant
        target_client_id = client_id or self._get_current_client_id()
        
        if soft_delete:
            # Soft delete: marcar como inactivo
            query = update(table).where(table.c[self.id_column] == entity_id).values(**{soft_delete_column: False})
            if self.tenant_column and target_client_id:
                query = query.where(table.c[self.tenant_column] == target_client_id)
        else:
            # Hard delete: eliminar físicamente
            query = delete(table).where(table.c[self.id_column] == entity_id)
            if self.tenant_column and target_client_id:
                query = query.where(table.c[self.tenant_column] == target_client_id)
        
        try:
            await execute_update(
                query,
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
    
    async def count(
        self,
        filters: Optional[Dict[str, Any]] = None,
        client_id: Optional[UUID] = None
    ) -> int:
        """
        Cuenta el número de entidades que cumplan con los filtros.
        
        ✅ FASE 2: Refactorizado para usar async.
        
        Args:
            filters: Diccionario con filtros {campo: valor}
            client_id: ID del cliente (opcional)
        
        Returns:
            Número de entidades
        """
        # ✅ FASE 2: Usar SQLAlchemy Core con async
        from app.infrastructure.database.tables import metadata
        from sqlalchemy import select, func
        
        table = metadata.tables.get(self.table_name)
        if not table:
            raise DatabaseError(
                detail=f"Tabla {self.table_name} no encontrada en metadata",
                internal_code="TABLE_NOT_FOUND"
            )
        
        query = select(func.count()).select_from(table)
        
        # Aplicar filtros personalizados
        if filters:
            for field, value in filters.items():
                if value is not None and field in table.c:
                    query = query.where(table.c[field] == value)
        
        # Aplicar filtro de tenant
        if self.tenant_column:
            target_client_id = client_id or self._get_current_client_id()
            if target_client_id:
                query = query.where(table.c[self.tenant_column] == target_client_id)
        
        try:
            result = await execute_query(
                query,
                connection_type=self.connection_type,
                client_id=client_id
            )
            return result[0]["count_1"] if result else 0
        except Exception as e:
            logger.error(f"Error en count para {self.table_name}: {str(e)}")
            raise DatabaseError(
                detail=f"Error al contar {self.table_name}: {str(e)}",
                internal_code="REPOSITORY_COUNT_ERROR"
            )
    
    async def exists(
        self,
        entity_id: Any,  # UUID o str
        client_id: Optional[UUID] = None
    ) -> bool:
        """
        Verifica si una entidad existe.
        
        ✅ FASE 2: Refactorizado para usar async.
        
        Args:
            entity_id: ID de la entidad
            client_id: ID del cliente (opcional)
        
        Returns:
            True si existe, False en caso contrario
        """
        result = await self.find_by_id(entity_id, client_id)
        return result is not None
