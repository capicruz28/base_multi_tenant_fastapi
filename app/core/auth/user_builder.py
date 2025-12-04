"""
Servicio para construir objetos Pydantic completos de usuario.

Este módulo se usa cuando se necesita el objeto completo UsuarioReadWithRoles,
por ejemplo en endpoints que requieren toda la información del usuario.

Separado de user_context.py para mantener la separación de responsabilidades:
- user_context.py: Contexto mínimo para autorización
- user_builder.py: Construcción de objetos completos cuando se necesitan
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
import json
import logging
from datetime import datetime

from app.modules.users.presentation.schemas import UsuarioReadWithRoles
from app.modules.rbac.presentation.schemas import RolRead
from app.infrastructure.database.queries_async import execute_auth_query
from app.infrastructure.database.tables import UsuarioTable, UsuarioRolTable, RolTable
from sqlalchemy import select, and_, or_

logger = logging.getLogger(__name__)


async def build_user_with_roles(
    username: str,
    request_cliente_id: Optional[UUID] = None
) -> Optional[UsuarioReadWithRoles]:
    """
    Construye un objeto UsuarioReadWithRoles completo con todos los datos del usuario.
    
    Esta función se usa cuando se necesita el objeto completo, no solo el contexto.
    Para validación rápida, usar get_user_auth_context() en su lugar.
    
    Args:
        username: Nombre de usuario
        request_cliente_id: ID del cliente del request
    
    Returns:
        UsuarioReadWithRoles si existe, None en caso contrario
    """
    try:
        # ✅ Obtener database_type del contexto para determinar si es BD dedicada
        from app.core.tenant.context import try_get_tenant_context
        
        tenant_context = try_get_tenant_context()
        database_type = tenant_context.database_type if tenant_context else "single"
        
        # 1. Obtener usuario básico
        # ✅ Para BD dedicadas, no filtrar por cliente_id (todos los usuarios pertenecen al mismo cliente)
        if database_type == "multi":
            # BD dedicada: buscar solo por nombre_usuario
            user_query = select(UsuarioTable).where(
                and_(
                    UsuarioTable.c.nombre_usuario == username,
                    UsuarioTable.c.es_eliminado == False
                )
            )
        elif request_cliente_id:
            # BD compartida: filtrar por cliente_id
            user_query = select(UsuarioTable).where(
                and_(
                    UsuarioTable.c.nombre_usuario == username,
                    UsuarioTable.c.es_eliminado == False,
                    UsuarioTable.c.cliente_id == request_cliente_id
                )
            )
        else:
            # Fallback: buscar sin filtro de cliente (para casos edge)
            user_query = select(UsuarioTable).where(
                and_(
                    UsuarioTable.c.nombre_usuario == username,
                    UsuarioTable.c.es_eliminado == False
                )
            )
        
        user_result = await execute_auth_query(user_query)
        
        if not user_result:
            return None
        
        if not user_result.get('es_activo', False):
            return None
        
        usuario_id = user_result.get('usuario_id')
        cliente_id = user_result.get('cliente_id')
        
        # ✅ CORRECCIÓN CRÍTICA: Para BD dedicadas, el cliente_id del usuario puede ser NULL o UUID nulo
        # Usar el cliente_id del contexto del tenant en su lugar
        if database_type == "multi":
            # Convertir cliente_id a UUID si es string para comparar
            user_cliente_id = cliente_id
            if user_cliente_id:
                if isinstance(user_cliente_id, str):
                    try:
                        user_cliente_id = UUID(user_cliente_id)
                    except (ValueError, AttributeError):
                        user_cliente_id = None
                elif not isinstance(user_cliente_id, UUID):
                    user_cliente_id = None
            
            # Verificar si es None o UUID nulo
            if not user_cliente_id or (isinstance(user_cliente_id, UUID) and user_cliente_id == UUID('00000000-0000-0000-0000-000000000000')):
                # Usar request_cliente_id (del contexto del tenant) en lugar del cliente_id del usuario
                if request_cliente_id:
                    cliente_id = request_cliente_id
                    logger.debug(
                        f"[USER_BUILDER] BD dedicada: cliente_id del usuario era NULL/nulo, "
                        f"usando cliente_id del contexto: {request_cliente_id}"
                    )
                else:
                    # Si no hay request_cliente_id, intentar obtenerlo del contexto
                    from app.core.tenant.context import try_get_current_client_id
                    cliente_id = try_get_current_client_id()
                    if cliente_id:
                        logger.debug(
                            f"[USER_BUILDER] BD dedicada: cliente_id del usuario era NULL/nulo, "
                            f"usando cliente_id del contexto: {cliente_id}"
                        )
                    else:
                        logger.warning(
                            f"[USER_BUILDER] BD dedicada: No se pudo obtener cliente_id del contexto para usuario '{username}'"
                        )
            else:
                cliente_id = user_cliente_id
        
        # 2. Obtener roles completos
        # ✅ Para BD dedicadas, no filtrar por cliente_id (todos los roles pertenecen al mismo tenant)
        if database_type == "multi":
            # BD dedicada: buscar roles sin filtrar por cliente_id
            roles_query = select(
                RolTable.c.rol_id,
                RolTable.c.nombre,
                RolTable.c.descripcion,
                RolTable.c.nivel_acceso,
                RolTable.c.codigo_rol,
                RolTable.c.es_activo,
                RolTable.c.fecha_creacion,
                RolTable.c.cliente_id
            ).select_from(
                UsuarioRolTable.join(RolTable, UsuarioRolTable.c.rol_id == RolTable.c.rol_id)
            ).where(
                and_(
                    UsuarioRolTable.c.usuario_id == usuario_id,
                    UsuarioRolTable.c.es_activo == True,
                    RolTable.c.es_activo == True
                )
            )
        else:
            # BD compartida: filtrar por cliente_id
            roles_cliente_id = cliente_id or request_cliente_id
            
            roles_query = select(
                RolTable.c.rol_id,
                RolTable.c.nombre,
                RolTable.c.descripcion,
                RolTable.c.nivel_acceso,
                RolTable.c.codigo_rol,
                RolTable.c.es_activo,
                RolTable.c.fecha_creacion,
                RolTable.c.cliente_id
            ).select_from(
                UsuarioRolTable.join(RolTable, UsuarioRolTable.c.rol_id == RolTable.c.rol_id)
            ).where(
                and_(
                    UsuarioRolTable.c.usuario_id == usuario_id,
                    UsuarioRolTable.c.es_activo == True,
                    RolTable.c.es_activo == True,
                    or_(
                        RolTable.c.cliente_id == roles_cliente_id if roles_cliente_id else False,
                        RolTable.c.cliente_id.is_(None)
                    )
                )
            )
        
        from app.infrastructure.database.queries_async import execute_query
        roles_result = await execute_query(roles_query, skip_tenant_validation=True)
        
        # 3. Construir lista de RolRead
        roles_list: List[RolRead] = []
        nivel_acceso = 1
        is_superadmin = False
        
        if roles_result:
            niveles = []
            for role_data in roles_result:
                try:
                    # Asegurar que fecha_creacion sea datetime
                    fecha_creacion = role_data.get('fecha_creacion')
                    if isinstance(fecha_creacion, str):
                        try:
                            fecha_creacion = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                        except:
                            fecha_creacion = datetime.now()
                    elif not isinstance(fecha_creacion, datetime):
                        fecha_creacion = datetime.now()
                    
                    # ✅ CORRECCIÓN: Normalizar cliente_id antes de crear RolRead
                    # En BD dedicadas, cliente_id puede ser NULL o UUID nulo
                    rol_cliente_id = role_data.get('cliente_id')
                    if rol_cliente_id is not None:
                        # Convertir a UUID si es string para comparar
                        if isinstance(rol_cliente_id, str):
                            try:
                                rol_cliente_id = UUID(rol_cliente_id)
                            except (ValueError, AttributeError):
                                rol_cliente_id = None
                        elif not isinstance(rol_cliente_id, UUID):
                            rol_cliente_id = None
                        
                        # Si es UUID nulo, establecer como None
                        if isinstance(rol_cliente_id, UUID) and rol_cliente_id == UUID('00000000-0000-0000-0000-000000000000'):
                            rol_cliente_id = None
                    
                    # Crear RolRead
                    rol_read = RolRead(
                        rol_id=role_data.get('rol_id'),
                        nombre=role_data.get('nombre'),
                        descripcion=role_data.get('descripcion'),
                        nivel_acceso=role_data.get('nivel_acceso', 1),
                        codigo_rol=role_data.get('codigo_rol'),
                        es_activo=bool(role_data.get('es_activo', True)),
                        fecha_creacion=fecha_creacion,
                        cliente_id=rol_cliente_id
                    )
                    roles_list.append(rol_read)
                    
                    # Calcular nivel máximo
                    nivel = role_data.get('nivel_acceso', 1)
                    if nivel:
                        niveles.append(nivel)
                    
                    # Verificar superadmin
                    if role_data.get('codigo_rol') == 'SUPER_ADMIN' and nivel == 5:
                        is_superadmin = True
                        
                except Exception as e:
                    logger.warning(f"Error construyendo RolRead: {e}")
                    continue
            
            if niveles:
                nivel_acceso = max(niveles)
        
        # 4. Determinar tipo de usuario
        user_type = determine_user_type(nivel_acceso, is_superadmin)
        
        # 5. Construir UsuarioReadWithRoles
        # ✅ Asegurar que cliente_id corregido se establezca explícitamente
        usuario_dict = {
            **user_result,
            'cliente_id': cliente_id,  # ✅ Establecer explícitamente el cliente_id corregido
            'access_level': nivel_acceso,
            'is_super_admin': is_superadmin,
            'user_type': user_type
        }
        
        usuario_pydantic = UsuarioReadWithRoles(**usuario_dict, roles=roles_list)
        
        return usuario_pydantic
        
    except Exception as e:
        logger.error(f"Error construyendo UsuarioReadWithRoles para '{username}': {e}", exc_info=True)
        return None


def determine_user_type(access_level: int, is_super_admin: bool) -> str:
    """
    Determina el tipo de usuario basado en nivel de acceso.
    
    Args:
        access_level: Nivel de acceso del usuario
        is_super_admin: Si es super admin
    
    Returns:
        str: Tipo de usuario: 'super_admin', 'tenant_admin', 'user'
    """
    if is_super_admin:
        return 'super_admin'
    elif access_level >= 4:
        return 'tenant_admin'
    else:
        return 'user'

