# app/modules/users/infrastructure/repositories/user_repository.py
"""
UserRepository: Repositorio para operaciones de usuarios.

✅ FASE 3: ARQUITECTURA - Repositorio para módulo Users
"""

from typing import Optional, Dict, Any, List
import logging

from app.infrastructure.database.repositories.base_repository import BaseRepository
from app.infrastructure.database.queries import execute_query
from app.infrastructure.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """
    Repositorio para operaciones de usuarios del módulo Users.
    
    Extiende BaseRepository con métodos específicos para gestión de usuarios.
    """
    
    def __init__(self):
        super().__init__(
            table_name="usuario",
            id_column="usuario_id",
            tenant_column="cliente_id",
            connection_type=DatabaseConnection.DEFAULT
        )
    
    def find_by_email(
        self,
        email: str,
        client_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un usuario por email.
        
        Args:
            email: Email del usuario
            client_id: ID del cliente (opcional)
        
        Returns:
            Diccionario con los datos del usuario o None si no existe
        """
        return self.find_all(
            filters={'correo': email, 'es_eliminado': 0},
            client_id=client_id,
            limit=1
        )[0] if self.find_all(
            filters={'correo': email, 'es_eliminado': 0},
            client_id=client_id,
            limit=1
        ) else None
    
    def find_by_dni(
        self,
        dni: str,
        client_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un usuario por DNI.
        
        Args:
            dni: DNI del usuario
            client_id: ID del cliente (opcional)
        
        Returns:
            Diccionario con los datos del usuario o None si no existe
        """
        results = self.find_all(
            filters={'dni': dni, 'es_eliminado': 0},
            client_id=client_id,
            limit=1
        )
        return results[0] if results else None
    
    def find_with_roles_and_permissions(
        self,
        usuario_id: int,
        client_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un usuario con sus roles y permisos asociados.
        
        Args:
            usuario_id: ID del usuario
            client_id: ID del cliente (opcional)
        
        Returns:
            Diccionario con los datos del usuario, roles y permisos
        """
        usuario = self.find_by_id(usuario_id, client_id)
        if not usuario:
            return None
        
        # Obtener roles
        query_roles = """
            SELECT 
                r.rol_id,
                r.codigo_rol,
                r.nombre as nombre_rol,
                r.descripcion as descripcion_rol,
                r.nivel_acceso,
                r.es_activo as rol_activo,
                ur.fecha_asignacion,
                ur.es_activo as asignacion_activa
            FROM rol r
            INNER JOIN usuario_rol ur ON r.rol_id = ur.rol_id
            WHERE ur.usuario_id = ?
            AND ur.es_activo = 1
            AND r.es_activo = 1
        """
        params_roles = (usuario_id,)
        
        if client_id:
            query_roles += " AND (r.cliente_id = ? OR r.cliente_id IS NULL)"
            params_roles = params_roles + (client_id,)
        
        try:
            roles = execute_query(
                query_roles,
                params_roles,
                connection_type=self.connection_type,
                client_id=client_id
            )
            
            # Obtener permisos de cada rol
            for rol in roles:
                query_permisos = """
                    SELECT 
                        p.permiso_id,
                        p.codigo_permiso,
                        p.nombre as nombre_permiso,
                        p.descripcion as descripcion_permiso,
                        p.es_activo as permiso_activo
                    FROM permiso p
                    INNER JOIN rol_permiso rp ON p.permiso_id = rp.permiso_id
                    WHERE rp.rol_id = ?
                    AND rp.es_activo = 1
                    AND p.es_activo = 1
                """
                permisos = execute_query(
                    query_permisos,
                    (rol['rol_id'],),
                    connection_type=self.connection_type,
                    client_id=client_id
                )
                rol['permisos'] = permisos
            
            usuario['roles'] = roles
            return usuario
        except Exception as e:
            logger.error(f"Error en find_with_roles_and_permissions: {str(e)}")
            usuario['roles'] = []
            return usuario
    
    def search_users(
        self,
        search_term: str,
        client_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca usuarios por término de búsqueda (nombre, apellido, correo, nombre_usuario).
        
        Args:
            search_term: Término de búsqueda
            client_id: ID del cliente (opcional)
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            Lista de usuarios que coinciden con la búsqueda
        """
        tenant_filter, tenant_params = self._build_tenant_filter(client_id)
        
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE es_eliminado = 0
            AND (
                nombre_usuario LIKE ? OR
                correo LIKE ? OR
                nombre LIKE ? OR
                apellido LIKE ?
            )
            {tenant_filter}
            ORDER BY nombre_usuario ASC
        """
        
        search_pattern = f"%{search_term}%"
        params = (search_pattern, search_pattern, search_pattern, search_pattern) + tenant_params
        
        if limit:
            query += f" OFFSET {offset or 0} ROWS FETCH NEXT {limit} ROWS ONLY"
        
        try:
            return execute_query(
                query,
                params,
                connection_type=self.connection_type,
                client_id=client_id
            )
        except Exception as e:
            logger.error(f"Error en search_users: {str(e)}")
            raise

