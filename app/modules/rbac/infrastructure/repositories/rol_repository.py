# app/modules/rbac/infrastructure/repositories/rol_repository.py
"""
RolRepository: Repositorio para operaciones de roles.

✅ FASE 3: ARQUITECTURA - Repositorio para módulo RBAC
"""

from typing import Optional, Dict, Any, List
import logging

from app.infrastructure.database.repositories.base_repository import BaseRepository
from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.connection_async import DatabaseConnection
from sqlalchemy import text

logger = logging.getLogger(__name__)


class RolRepository(BaseRepository):
    """
    Repositorio para operaciones de roles.
    
    Extiende BaseRepository con métodos específicos para gestión de roles.
    """
    
    def __init__(self):
        super().__init__(
            table_name="rol",
            id_column="rol_id",
            tenant_column="cliente_id",
            connection_type=DatabaseConnection.DEFAULT
        )
    
    def find_by_codigo(
        self,
        codigo_rol: str,
        client_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un rol por código.
        
        Args:
            codigo_rol: Código del rol
            client_id: ID del cliente (opcional)
        
        Returns:
            Diccionario con los datos del rol o None si no existe
        """
        results = self.find_all(
            filters={'codigo_rol': codigo_rol, 'es_activo': 1},
            client_id=client_id,
            limit=1
        )
        return results[0] if results else None
    
    def find_by_nombre(
        self,
        nombre: str,
        client_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un rol por nombre.
        
        Args:
            nombre: Nombre del rol
            client_id: ID del cliente (opcional)
        
        Returns:
            Diccionario con los datos del rol o None si no existe
        """
        results = self.find_all(
            filters={'nombre': nombre, 'es_activo': 1},
            client_id=client_id,
            limit=1
        )
        return results[0] if results else None
    
    async def find_with_permisos(
        self,
        rol_id: int,
        client_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un rol con sus permisos asociados.
        
        Args:
            rol_id: ID del rol
            client_id: ID del cliente (opcional)
        
        Returns:
            Diccionario con los datos del rol y lista de permisos
        """
        rol = self.find_by_id(rol_id, client_id)
        if not rol:
            return None
        
        # Obtener permisos del rol
        query_permisos = """
            SELECT 
                p.permiso_id,
                p.codigo_permiso,
                p.nombre as nombre_permiso,
                p.descripcion as descripcion_permiso,
                p.es_activo as permiso_activo,
                rp.es_activo as asignacion_activa
            FROM permiso p
            INNER JOIN rol_permiso rp ON p.permiso_id = rp.permiso_id
            WHERE rp.rol_id = :rol_id
            AND rp.es_activo = 1
            AND p.es_activo = 1
        """
        
        try:
            permisos = await execute_query(
                text(query_permisos).bindparams(rol_id=rol_id),
                connection_type=self.connection_type,
                client_id=client_id
            )
            rol['permisos'] = permisos
            return rol
        except Exception as e:
            logger.error(f"Error en find_with_permisos: {str(e)}")
            rol['permisos'] = []
            return rol
    
    async def find_roles_by_usuario(
        self,
        usuario_id: int,
        client_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca todos los roles asignados a un usuario.
        
        Args:
            usuario_id: ID del usuario
            client_id: ID del cliente (opcional)
        
        Returns:
            Lista de roles asignados al usuario
        """
        tenant_filter, tenant_params = self._build_tenant_filter(client_id)
        
        query = f"""
            SELECT 
                r.*,
                ur.fecha_asignacion,
                ur.es_activo as asignacion_activa
            FROM {self.table_name} r
            INNER JOIN usuario_rol ur ON r.rol_id = ur.rol_id
            WHERE ur.usuario_id = :usuario_id
            AND ur.es_activo = 1
            AND r.es_activo = 1
            {tenant_filter}
            ORDER BY r.nombre ASC
        """
        bind_params = {"usuario_id": usuario_id}
        # TODO: Convertir tenant_params a bind_params si es necesario
        
        try:
            return await execute_query(
                text(query).bindparams(**bind_params),
                connection_type=self.connection_type,
                client_id=client_id
            )
        except Exception as e:
            logger.error(f"Error en find_roles_by_usuario: {str(e)}")
            raise

