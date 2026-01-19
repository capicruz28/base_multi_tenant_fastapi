"""
Servicio ligero para obtener contexto de usuario autenticado.

Este módulo proporciona funciones optimizadas para obtener solo el contexto
mínimo necesario del usuario autenticado, sin construir objetos de dominio completos.

Objetivo: Reducir el acoplamiento entre deps.py y los servicios de módulos.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from dataclasses import dataclass
import logging

from app.infrastructure.database.queries_async import execute_auth_query, execute_query
from app.infrastructure.database.tables import UsuarioTable, UsuarioRolTable, RolTable
from sqlalchemy import select, func, and_, or_

logger = logging.getLogger(__name__)


@dataclass
class CurrentUserContext:
    """
    Contexto mínimo del usuario autenticado.
    
    Contiene solo la información esencial necesaria para autorización
    y validación de tenant, sin objetos de dominio completos.
    """
    usuario_id: UUID
    cliente_id: Optional[UUID]
    nombre_usuario: str
    es_activo: bool
    is_superadmin: bool
    nivel_acceso: int
    roles: List[str]  # Solo nombres de roles, no objetos completos


async def get_user_auth_context(
    username: str,
    request_cliente_id: Optional[UUID] = None
) -> Optional[CurrentUserContext]:
    """
    Obtiene el contexto mínimo del usuario autenticado.
    
    Esta función es optimizada y retorna solo la información esencial:
    - usuario_id, cliente_id, nombre_usuario, es_activo
    - is_superadmin, nivel_acceso
    - roles (solo nombres)
    
    No construye objetos Pydantic completos ni objetos de dominio.
    
    Args:
        username: Nombre de usuario del token JWT
        request_cliente_id: ID del cliente del request (del contexto de tenant)
    
    Returns:
        CurrentUserContext si el usuario existe y está activo, None en caso contrario
    
    Raises:
        RuntimeError: Si no se puede obtener el contexto de tenant y es necesario
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
            user_result = await execute_auth_query(user_query)
        elif request_cliente_id:
            # BD compartida: primero intentar con cliente_id del tenant
            user_query = select(UsuarioTable).where(
                and_(
                    UsuarioTable.c.nombre_usuario == username,
                    UsuarioTable.c.es_eliminado == False,
                    UsuarioTable.c.cliente_id == request_cliente_id
                )
            )
            user_result = await execute_auth_query(user_query)
            
            # ✅ CORRECCIÓN: Si no se encuentra con cliente_id, intentar sin filtro
            # (para usuarios del sistema como superadmin que pueden tener cliente_id NULL o diferente)
            if not user_result:
                logger.debug(f"Usuario '{username}' no encontrado con cliente_id {request_cliente_id}, intentando sin filtro de cliente")
                user_query_fallback = select(UsuarioTable).where(
                    and_(
                        UsuarioTable.c.nombre_usuario == username,
                        UsuarioTable.c.es_eliminado == False
                    )
                )
                user_result = await execute_auth_query(user_query_fallback)
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
            logger.warning(f"Usuario '{username}' no encontrado en BD")
            return None
        
        usuario_id = user_result.get('usuario_id')
        cliente_id = user_result.get('cliente_id')
        es_activo = user_result.get('es_activo', False)
        
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
                        f"[USER_CONTEXT] BD dedicada: cliente_id del usuario era NULL/nulo, "
                        f"usando cliente_id del contexto: {request_cliente_id}"
                    )
                else:
                    # Si no hay request_cliente_id, intentar obtenerlo del contexto
                    from app.core.tenant.context import try_get_current_client_id
                    cliente_id = try_get_current_client_id()
                    if cliente_id:
                        logger.debug(
                            f"[USER_CONTEXT] BD dedicada: cliente_id del usuario era NULL/nulo, "
                            f"usando cliente_id del contexto: {cliente_id}"
                        )
                    else:
                        logger.warning(
                            f"[USER_CONTEXT] BD dedicada: No se pudo obtener cliente_id del contexto para usuario '{username}'"
                        )
            else:
                cliente_id = user_cliente_id
        
        if not es_activo:
            logger.warning(f"Usuario '{username}' inactivo")
            return None
        
        # 2. Obtener roles y niveles en una sola query
        # ✅ Para BD dedicadas, no filtrar por cliente_id (todos los roles pertenecen al mismo tenant)
        if database_type == "multi":
            # BD dedicada: buscar roles sin filtrar por cliente_id
            roles_query = select(
                RolTable.c.rol_id,
                RolTable.c.nombre,
                RolTable.c.nivel_acceso,
                RolTable.c.codigo_rol
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
            # Usar cliente_id del usuario o request_cliente_id para filtrar roles
            roles_cliente_id = cliente_id or request_cliente_id
            
            roles_query = select(
                RolTable.c.rol_id,
                RolTable.c.nombre,
                RolTable.c.nivel_acceso,
                RolTable.c.codigo_rol
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
        
        # execute_query retorna lista, execute_auth_query retorna un solo registro
        # ✅ CORRECCIÓN SEGURIDAD: Eliminado skip_tenant_validation=True
        # - Para BD dedicadas (multi): La query no filtra por cliente_id (correcto, todos los roles son del mismo tenant)
        # - Para BD compartidas (single): La query YA filtra por cliente_id (líneas 198-200)
        # El sistema de validación automática detectará que las queries son seguras
        roles_result = await execute_query(roles_query, client_id=cliente_id or request_cliente_id)
        
        # 3. Calcular niveles y roles
        roles_list: List[str] = []
        nivel_acceso = 1  # Default
        is_superadmin = False
        
        if roles_result:
            niveles = []
            for role in roles_result:
                role_name = role.get('nombre')
                if role_name:
                    roles_list.append(role_name)
                
                nivel = role.get('nivel_acceso', 1)
                if nivel:
                    niveles.append(nivel)
                
                # Verificar si es SUPER_ADMIN
                codigo_rol = role.get('codigo_rol')
                if codigo_rol == 'SUPER_ADMIN' and nivel == 5:
                    is_superadmin = True
            
            if niveles:
                nivel_acceso = max(niveles)
        
        # 4. Construir y retornar contexto
        context = CurrentUserContext(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            nombre_usuario=username,
            es_activo=es_activo,
            is_superadmin=is_superadmin,
            nivel_acceso=nivel_acceso,
            roles=roles_list
        )
        
        logger.debug(
            f"Contexto de usuario obtenido: {username}, "
            f"cliente_id={cliente_id}, nivel={nivel_acceso}, "
            f"superadmin={is_superadmin}"
        )
        
        return context
        
    except Exception as e:
        logger.error(f"Error obteniendo contexto de usuario '{username}': {e}", exc_info=True)
        return None


async def validate_tenant_access(
    context: CurrentUserContext,
    request_cliente_id: Optional[UUID]
) -> bool:
    """
    Valida que el usuario tenga acceso al tenant del request.
    
    Reglas:
    - SuperAdmin puede acceder a cualquier tenant
    - Usuarios regulares solo pueden acceder a su propio tenant
    
    Args:
        context: Contexto del usuario autenticado
        request_cliente_id: ID del cliente del request
    
    Returns:
        True si tiene acceso, False en caso contrario
    """
    # SuperAdmin puede acceder a cualquier tenant
    if context.is_superadmin:
        return True
    
    # Usuario regular: debe coincidir el tenant
    if context.cliente_id is None:
        logger.warning(
            f"Usuario regular '{context.nombre_usuario}' tiene cliente_id NULL"
        )
        return False
    
    if request_cliente_id is None:
        logger.warning(
            f"Request no tiene cliente_id para validar acceso de '{context.nombre_usuario}'"
        )
        return False
    
    return context.cliente_id == request_cliente_id


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

