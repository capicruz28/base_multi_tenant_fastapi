# app/modules/auth/infrastructure/repositories/usuario_repository.py
"""
UsuarioRepository: Repositorio para operaciones de usuarios relacionadas con autenticación.

✅ FASE 3: ARQUITECTURA - Repositorio para módulo Auth
"""

from typing import Optional, Dict, Any, List
import logging

from app.infrastructure.database.repositories.base_repository import BaseRepository
from app.infrastructure.database.queries_async import execute_query, execute_update
from app.infrastructure.database.connection_async import DatabaseConnection
from app.core.tenant.context import get_current_client_id
from sqlalchemy import text

logger = logging.getLogger(__name__)


class UsuarioRepository(BaseRepository):
    """
    Repositorio para operaciones de usuarios relacionadas con autenticación.
    
    Maneja consultas específicas de autenticación como:
    - Buscar usuario por username/email
    - Verificar credenciales
    - Obtener usuario con roles y permisos
    """
    
    def __init__(self):
        super().__init__(
            table_name="usuario",
            id_column="usuario_id",
            tenant_column="cliente_id",
            connection_type=DatabaseConnection.DEFAULT
        )
    
    async def find_by_username_or_email(
        self,
        username_or_email: str,
        client_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un usuario por username o email.
        
        Args:
            username_or_email: Username o email del usuario
            client_id: ID del cliente (opcional)
        
        Returns:
            Diccionario con los datos del usuario o None si no existe
        """
        target_client_id = client_id or self._get_current_client_id()
        
        query = """
            SELECT * FROM usuario
            WHERE (nombre_usuario = :username_or_email OR email = :username_or_email)
            AND es_activo = 1
        """
        bind_params = {"username_or_email": username_or_email}
        
        # Agregar filtro de tenant si aplica
        if target_client_id:
            query += " AND cliente_id = :client_id"
            bind_params["client_id"] = target_client_id
        
        try:
            results = await execute_query(
                text(query).bindparams(**bind_params),
                connection_type=self.connection_type,
                client_id=client_id
            )
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error en find_by_username_or_email: {str(e)}")
            raise
    
    async def find_by_username(
        self,
        username: str,
        client_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un usuario por username.
        
        Args:
            username: Username del usuario
            client_id: ID del cliente (opcional)
        
        Returns:
            Diccionario con los datos del usuario o None si no existe
        """
        target_client_id = client_id or self._get_current_client_id()
        
        query = """
            SELECT * FROM usuario
            WHERE nombre_usuario = :username
            AND es_activo = 1
        """
        bind_params = {"username": username}
        
        if target_client_id:
            query += " AND cliente_id = :client_id"
            bind_params["client_id"] = target_client_id
        
        try:
            results = await execute_query(
                text(query).bindparams(**bind_params),
                connection_type=self.connection_type,
                client_id=client_id
            )
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error en find_by_username: {str(e)}")
            raise
    
    async def find_with_roles(
        self,
        usuario_id: int,
        client_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un usuario con sus roles asociados.
        
        Args:
            usuario_id: ID del usuario
            client_id: ID del cliente (opcional)
        
        Returns:
            Diccionario con los datos del usuario y lista de roles
        """
        target_client_id = client_id or self._get_current_client_id()
        
        # Query principal del usuario
        usuario = self.find_by_id(usuario_id, client_id)
        if not usuario:
            return None
        
        # Query de roles
        query_roles = """
            SELECT 
                r.rol_id,
                r.codigo_rol,
                r.nombre_rol,
                r.descripcion,
                r.es_activo,
                ur.es_activo as asignacion_activa
            FROM rol r
            INNER JOIN usuario_rol ur ON r.rol_id = ur.rol_id
            WHERE ur.usuario_id = :usuario_id
            AND ur.es_activo = 1
            AND r.es_activo = 1
        """
        bind_params_roles = {"usuario_id": usuario_id}
        
        if target_client_id:
            query_roles += " AND r.cliente_id = :client_id"
            bind_params_roles["client_id"] = target_client_id
        
        try:
            roles = await execute_query(
                text(query_roles).bindparams(**bind_params_roles),
                connection_type=self.connection_type,
                client_id=client_id
            )
            usuario['roles'] = roles
            return usuario
        except Exception as e:
            logger.error(f"Error en find_with_roles: {str(e)}")
            # Retornar usuario sin roles si falla la query de roles
            usuario['roles'] = []
            return usuario
    
    async def update_last_login(
        self,
        usuario_id: int,
        client_id: Optional[int] = None
    ) -> bool:
        """
        Actualiza la fecha del último login del usuario.
        
        Args:
            usuario_id: ID del usuario
            client_id: ID del cliente (opcional)
        
        Returns:
            True si se actualizó correctamente
        """
        from datetime import datetime
        
        query = f"""
            UPDATE {self.table_name}
            SET ultimo_acceso = GETDATE()
            WHERE {self.id_column} = :usuario_id
        """
        bind_params = {"usuario_id": usuario_id}
        
        # Agregar filtro de tenant
        tenant_filter, tenant_params = self._build_tenant_filter(client_id)
        query += tenant_filter
        # TODO: Convertir tenant_params a bind_params si es necesario
        
        try:
            await execute_update(
                text(query).bindparams(**bind_params),
                connection_type=self.connection_type,
                client_id=client_id
            )
            return True
        except Exception as e:
            logger.error(f"Error en update_last_login: {str(e)}")
            return False

