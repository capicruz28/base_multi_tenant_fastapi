# app/modules/rbac/infrastructure/repositories/permiso_repository.py
"""
PermisoRepository: Repositorio para operaciones de permisos.

✅ FASE 3: ARQUITECTURA - Repositorio para módulo RBAC
"""

from typing import Optional, Dict, Any, List
import logging

from app.infrastructure.database.repositories.base_repository import BaseRepository
from app.infrastructure.database.queries import execute_query
from app.infrastructure.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class PermisoRepository(BaseRepository):
    """
    Repositorio para operaciones de permisos.
    
    Extiende BaseRepository con métodos específicos para gestión de permisos.
    """
    
    def __init__(self):
        super().__init__(
            table_name="permiso",
            id_column="permiso_id",
            tenant_column=None,  # Los permisos no tienen cliente_id (son globales)
            connection_type=DatabaseConnection.DEFAULT
        )
    
    def find_by_codigo(
        self,
        codigo_permiso: str
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un permiso por código.
        
        Args:
            codigo_permiso: Código del permiso
        
        Returns:
            Diccionario con los datos del permiso o None si no existe
        """
        results = self.find_all(
            filters={'codigo_permiso': codigo_permiso, 'es_activo': 1},
            limit=1
        )
        return results[0] if results else None
    
    def find_permisos_by_rol(
        self,
        rol_id: int
    ) -> List[Dict[str, Any]]:
        """
        Busca todos los permisos asignados a un rol.
        
        Args:
            rol_id: ID del rol
        
        Returns:
            Lista de permisos asignados al rol
        """
        query = """
            SELECT 
                p.*,
                rp.es_activo as asignacion_activa
            FROM permiso p
            INNER JOIN rol_permiso rp ON p.permiso_id = rp.permiso_id
            WHERE rp.rol_id = ?
            AND rp.es_activo = 1
            AND p.es_activo = 1
            ORDER BY p.nombre ASC
        """
        
        try:
            return execute_query(
                query,
                (rol_id,),
                connection_type=self.connection_type
            )
        except Exception as e:
            logger.error(f"Error en find_permisos_by_rol: {str(e)}")
            raise
    
    def find_permisos_by_usuario(
        self,
        usuario_id: int,
        client_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca todos los permisos de un usuario (a través de sus roles).
        
        Args:
            usuario_id: ID del usuario
            client_id: ID del cliente (opcional)
        
        Returns:
            Lista de permisos del usuario
        """
        query = """
            SELECT DISTINCT
                p.*
            FROM permiso p
            INNER JOIN rol_permiso rp ON p.permiso_id = rp.permiso_id
            INNER JOIN rol r ON rp.rol_id = r.rol_id
            INNER JOIN usuario_rol ur ON r.rol_id = ur.rol_id
            WHERE ur.usuario_id = ?
            AND ur.es_activo = 1
            AND r.es_activo = 1
            AND rp.es_activo = 1
            AND p.es_activo = 1
        """
        params = (usuario_id,)
        
        if client_id:
            query += " AND (r.cliente_id = ? OR r.cliente_id IS NULL)"
            params = params + (client_id,)
        
        try:
            return execute_query(
                query,
                params,
                connection_type=self.connection_type,
                client_id=client_id
            )
        except Exception as e:
            logger.error(f"Error en find_permisos_by_usuario: {str(e)}")
            raise

