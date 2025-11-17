# app/core/authorization.py
"""
Sistema de autorización y control de acceso para la aplicación.

Este módulo proporciona utilidades para la validación de roles y permisos,
detección automática de tipos de usuario, y protección de endpoints mediante
dependencias de FastAPI.

Características principales:
- Detección automática de Super Admin vs Tenant Admin vs Usuario normal
- Validación de permisos basada en roles y permisos individuales
- Sistema de autorización jerárquico y flexible
- Integración seamless con FastAPI dependencies
- Logging detallado para auditoría de seguridad

Estructura de autorización:
┌─────────────────┐
│   SUPER ADMIN   │ ← Acceso completo al sistema
├─────────────────┤
│   TENANT ADMIN  │ ← Acceso completo dentro de su tenant
├─────────────────┤
│  USUARIO NORMAL │ ← Acceso limitado según roles/permisos
└─────────────────┘
"""

from functools import wraps
from typing import List, Optional, Callable, Any, Dict
from fastapi import HTTPException, status, Depends
import logging

# 🗄️ IMPORTACIONES DE SCHEMAS Y MODELOS
from app.schemas.auth import UserWithRolesAndPermissions
from app.api.dependencies import get_current_active_user

# 🔐 CONSTANTES DE ROLES Y PERMISOS
SUPER_ADMIN_ROLE = "SuperAdministrador"
TENANT_ADMIN_ROLE = "AdministradorTenant"

# Permisos del sistema organizados por módulo
PERMISOS_SISTEMA = {
    "usuarios": ["crear", "leer", "actualizar", "eliminar", "administrar"],
    "roles": ["crear", "leer", "actualizar", "eliminar", "asignar"],
    "clientes": ["crear", "leer", "actualizar", "eliminar", "configurar"],
    "reportes": ["generar", "leer", "exportar", "administrar"],
    "configuracion": ["leer", "actualizar", "administrar"],
    "auditoria": ["leer", "exportar"]
}

logger = logging.getLogger(__name__)

class AuthorizationError(HTTPException):
    """
    Excepción personalizada para errores de autorización.
    
    Proporciona mensajes de error claros y específicos para ayudar
    en el desarrollo y debugging de problemas de permisos.
    """
    
    def __init__(
        self, 
        detail: str = "Acceso no autorizado",
        internal_code: str = "AUTHORIZATION_ERROR"
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )
        self.internal_code = internal_code

def get_user_type(user: UserWithRolesAndPermissions) -> str:
    """
    Detecta automáticamente el tipo de usuario basado en sus roles.
    
    🎯 ALGORITMO DE DETECCIÓN:
    1. Si tiene rol 'SuperAdministrador' → SUPER ADMIN
    2. Si tiene rol 'AdministradorTenant' → TENANT ADMIN  
    3. Cualquier otro caso → USUARIO NORMAL
    
    Args:
        user: Instancia de UserWithRolesAndPermissions con datos del usuario
        
    Returns:
        str: Tipo de usuario detectado ('super_admin', 'tenant_admin', 'usuario_normal')
        
    Raises:
        ValueError: Si los datos del usuario son inválidos
    """
    if not user or not hasattr(user, 'roles'):
        raise ValueError("Usuario inválido para detección de tipo")
    
    logger.debug(f"Detectando tipo de usuario para: {user.nombre_usuario}")
    logger.debug(f"Roles del usuario: {[rol.nombre for rol in user.roles]}")
    
    # 🔍 BUSCAR ROLES DE ADMINISTRACIÓN
    nombres_roles = [rol.nombre for rol in user.roles]
    
    if SUPER_ADMIN_ROLE in nombres_roles:
        user_type = "super_admin"
        logger.info(f"Usuario {user.nombre_usuario} detectado como SUPER ADMIN")
        
    elif TENANT_ADMIN_ROLE in nombres_roles:
        user_type = "tenant_admin" 
        logger.info(f"Usuario {user.nombre_usuario} detectado como TENANT ADMIN")
        
    else:
        user_type = "usuario_normal"
        logger.info(f"Usuario {user.nombre_usuario} detectado como USUARIO NORMAL")
    
    return user_type

def has_role(user: UserWithRolesAndPermissions, role_name: str) -> bool:
    """
    Verifica si un usuario tiene un rol específico asignado y activo.
    
    Args:
        user: Usuario a verificar
        role_name: Nombre del rol a buscar
        
    Returns:
        bool: True si el usuario tiene el rol activo, False en caso contrario
    """
    if not user or not user.roles:
        return False
    
    for rol in user.roles:
        if (rol.nombre == role_name and 
            rol.es_activo and 
            getattr(rol, 'fecha_asignacion', None) is not None):
            return True
    
    return False

def has_any_role(user: UserWithRolesAndPermissions, role_names: List[str]) -> bool:
    """
    Verifica si un usuario tiene al menos uno de los roles especificados.
    
    Args:
        user: Usuario a verificar
        role_names: Lista de nombres de roles a buscar
        
    Returns:
        bool: True si el usuario tiene al menos uno de los roles
    """
    return any(has_role(user, role_name) for role_name in role_names)

def has_permission(user: UserWithRolesAndPermissions, permission: str) -> bool:
    """
    Verifica si un usuario tiene un permiso específico.
    
    🎯 BÚSQUEDA JERÁRQUICA:
    1. Super Admin tiene todos los permisos automáticamente
    2. Busca en la lista de permisos individuales del usuario
    3. Considera permisos implícitos por roles de administración
    
    Args:
        user: Usuario a verificar
        permission: Permiso a verificar (formato: 'modulo.accion')
        
    Returns:
        bool: True si el usuario tiene el permiso
    """
    if not user:
        return False
    
    # ✅ SUPER ADMIN TIENE ACCESO COMPLETO
    if get_user_type(user) == "super_admin":
        logger.debug(f"Super Admin {user.nombre_usuario} tiene acceso completo al permiso: {permission}")
        return True
    
    # 🔍 VERIFICAR EN PERMISOS EXPLÍCITOS
    permisos_usuario = [permiso.nombre for permiso in user.permisos]
    
    if permission in permisos_usuario:
        logger.debug(f"Usuario {user.nombre_usuario} tiene permiso explícito: {permission}")
        return True
    
    # 🎯 VERIFICAR PERMISOS IMPLÍCITOS POR ROLES DE ADMIN
    if get_user_type(user) == "tenant_admin":
        # Tenant Admin tiene acceso completo dentro de su tenant
        # Excepto para operaciones de sistema global
        permisos_restringidos_tenant_admin = [
            "clientes.crear", "clientes.eliminar", "system.configurar"
        ]
        
        if permission not in permisos_restringidos_tenant_admin:
            logger.debug(f"Tenant Admin {user.nombre_usuario} tiene acceso implícito: {permission}")
            return True
    
    logger.warning(f"Usuario {user.nombre_usuario} NO tiene permiso: {permission}")
    return False

def has_any_permission(user: UserWithRolesAndPermissions, permissions: List[str]) -> bool:
    """
    Verifica si un usuario tiene al menos uno de los permisos especificados.
    
    Args:
        user: Usuario a verificar
        permissions: Lista de permisos a verificar
        
    Returns:
        bool: True si el usuario tiene al menos uno de los permisos
    """
    return any(has_permission(user, perm) for perm in permissions)

def require_super_admin() -> Callable:
    """
    Dependency que requiere que el usuario sea Super Administrador.
    
    🛡️ PROTECCIÓN MÁXIMA:
    - Solo usuarios con rol 'SuperAdministrador'
    - Acceso completo al sistema
    - Operaciones críticas y configuración global
    
    Returns:
        Callable: Dependencia de FastAPI que valida el rol
        
    Raises:
        AuthorizationError: Si el usuario no es Super Admin
    """
    def dependency(current_user: UserWithRolesAndPermissions = Depends(get_current_active_user)) -> UserWithRolesAndPermissions:
        """
        Valida que el usuario actual sea Super Administrador.
        
        Args:
            current_user: Usuario autenticado obtenido del token JWT
            
        Returns:
            UserWithRolesAndPermissions: Usuario validado
            
        Raises:
            AuthorizationError: Si el usuario no tiene permisos de Super Admin
        """
        logger.info(f"Validando Super Admin para usuario: {current_user.nombre_usuario}")
        
        if get_user_type(current_user) != "super_admin":
            logger.warning(
                f"Intento de acceso no autorizado a endpoint Super Admin por: {current_user.nombre_usuario}"
            )
            raise AuthorizationError(
                detail="Se requieren privilegios de Super Administrador para acceder a este recurso",
                internal_code="SUPER_ADMIN_REQUIRED"
            )
        
        logger.info(f"Acceso Super Admin autorizado para: {current_user.nombre_usuario}")
        return current_user
    
    return dependency

def require_tenant_admin() -> Callable:
    """
    Dependency que requiere que el usuario sea Tenant Admin o Super Admin.
    
    🏢 ALCANCE TENANT:
    - Super Admin (acceso completo)
    - Tenant Admin (acceso dentro de su tenant)
    - Gestión de usuarios y configuración del tenant
    
    Returns:
        Callable: Dependencia de FastAPI que valida el rol
        
    Raises:
        AuthorizationError: Si el usuario no tiene permisos suficientes
    """
    def dependency(current_user: UserWithRolesAndPermissions = Depends(get_current_active_user)) -> UserWithRolesAndPermissions:
        """
        Valida que el usuario actual sea Tenant Admin o Super Admin.
        
        Args:
            current_user: Usuario autenticado obtenido del token JWT
            
        Returns:
            UserWithRolesAndPermissions: Usuario validado
            
        Raises:
            AuthorizationError: Si el usuario no tiene permisos de administración
        """
        logger.info(f"Validando Tenant Admin para usuario: {current_user.nombre_usuario}")
        
        user_type = get_user_type(current_user)
        
        if user_type not in ["super_admin", "tenant_admin"]:
            logger.warning(
                f"Intento de acceso no autorizado a endpoint Tenant Admin por: {current_user.nombre_usuario}"
            )
            raise AuthorizationError(
                detail="Se requieren privilegios de Administrador para acceder a este recurso",
                internal_code="TENANT_ADMIN_REQUIRED"
            )
        
        logger.info(f"Acceso Tenant Admin autorizado para: {current_user.nombre_usuario} ({user_type})")
        return current_user
    
    return dependency

def require_permission(permission: str) -> Callable:
    """
    Dependency que requiere un permiso específico.
    
    🔒 AUTORIZACIÓN GRANULAR:
    - Verifica permisos individuales del usuario
    - Super Admin siempre tiene acceso
    - Flexibilidad para permisos específicos
    
    Args:
        permission: Permiso requerido (formato: 'modulo.accion')
        
    Returns:
        Callable: Dependencia de FastAPI que valida el permiso
        
    Raises:
        AuthorizationError: Si el usuario no tiene el permiso
    """
    def dependency(current_user: UserWithRolesAndPermissions = Depends(get_current_active_user)) -> UserWithRolesAndPermissions:
        """
        Valida que el usuario actual tenga el permiso específico.
        
        Args:
            current_user: Usuario autenticado obtenido del token JWT
            
        Returns:
            UserWithRolesAndPermissions: Usuario validado
            
        Raises:
            AuthorizationError: Si el usuario no tiene el permiso requerido
        """
        logger.info(f"Validando permiso '{permission}' para usuario: {current_user.nombre_usuario}")
        
        if not has_permission(current_user, permission):
            logger.warning(
                f"Intento de acceso sin permiso '{permission}' por: {current_user.nombre_usuario}"
            )
            raise AuthorizationError(
                detail=f"No tiene permisos suficientes para realizar esta acción. Se requiere: {permission}",
                internal_code="PERMISSION_DENIED"
            )
        
        logger.info(f"Permiso '{permission}' autorizado para: {current_user.nombre_usuario}")
        return current_user
    
    return dependency

def require_any_permission(permissions: List[str]) -> Callable:
    """
    Dependency que requiere al menos uno de los permisos especificados.
    
    Args:
        permissions: Lista de permisos, al menos uno requerido
        
    Returns:
        Callable: Dependencia de FastAPI que valida los permisos
        
    Raises:
        AuthorizationError: Si el usuario no tiene ninguno de los permisos
    """
    def dependency(current_user: UserWithRolesAndPermissions = Depends(get_current_active_user)) -> UserWithRolesAndPermissions:
        """
        Valida que el usuario actual tenga al menos uno de los permisos.
        
        Args:
            current_user: Usuario autenticado obtenido del token JWT
            
        Returns:
            UserWithRolesAndPermissions: Usuario validado
            
        Raises:
            AuthorizationError: Si el usuario no tiene ninguno de los permisos
        """
        logger.info(f"Validando permisos alternativos {permissions} para usuario: {current_user.nombre_usuario}")
        
        if not has_any_permission(current_user, permissions):
            logger.warning(
                f"Intento de acceso sin permisos alternativos {permissions} por: {current_user.nombre_usuario}"
            )
            raise AuthorizationError(
                detail=f"No tiene permisos suficientes. Se requiere al menos uno de: {', '.join(permissions)}",
                internal_code="ANY_PERMISSION_DENIED"
            )
        
        logger.info(f"Permisos alternativos autorizados para: {current_user.nombre_usuario}")
        return current_user
    
    return dependency

def require_any_role(role_names: List[str]) -> Callable:
    """
    Dependency que requiere al menos uno de los roles especificados.
    
    Args:
        role_names: Lista de nombres de roles requeridos
        
    Returns:
        Callable: Dependencia de FastAPI que valida los roles
        
    Raises:
        AuthorizationError: Si el usuario no tiene ninguno de los roles
    """
    def dependency(current_user: UserWithRolesAndPermissions = Depends(get_current_active_user)) -> UserWithRolesAndPermissions:
        """
        Valida que el usuario actual tenga al menos uno de los roles.
        
        Args:
            current_user: Usuario autenticado obtenido del token JWT
            
        Returns:
            UserWithRolesAndPermissions: Usuario validado
            
        Raises:
            AuthorizationError: Si el usuario no tiene ninguno de los roles
        """
        logger.info(f"Validando roles alternativos {role_names} para usuario: {current_user.nombre_usuario}")
        
        if not has_any_role(current_user, role_names):
            logger.warning(
                f"Intento de acceso sin roles alternativos {role_names} por: {current_user.nombre_usuario}"
            )
            raise AuthorizationError(
                detail=f"No tiene los roles necesarios. Se requiere al menos uno de: {', '.join(role_names)}",
                internal_code="ANY_ROLE_DENIED"
            )
        
        logger.info(f"Roles alternativos autorizados para: {current_user.nombre_usuario}")
        return current_user
    
    return dependency

# 🎯 DECORADORES PARA USO EN ENDPOINTS (alternativa a dependencies)
def super_admin_required(func: Callable) -> Callable:
    """
    Decorador que requiere Super Admin para el endpoint.
    
    Uso:
    @super_admin_required
    @router.get("/admin-endpoint")
    async def admin_endpoint(current_user: User = Depends(get_current_active_user)):
        ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Buscar el current_user en los kwargs
        current_user = None
        for arg_name, arg_value in kwargs.items():
            if isinstance(arg_value, UserWithRolesAndPermissions):
                current_user = arg_value
                break
        
        if not current_user:
            raise AuthorizationError(detail="Usuario no autenticado")
        
        # Validar Super Admin
        if get_user_type(current_user) != "super_admin":
            raise AuthorizationError(
                detail="Se requieren privilegios de Super Administrador",
                internal_code="SUPER_ADMIN_REQUIRED_DECORATOR"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper

def tenant_admin_required(func: Callable) -> Callable:
    """
    Decorador que requiere Tenant Admin o Super Admin para el endpoint.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = None
        for arg_name, arg_value in kwargs.items():
            if isinstance(arg_value, UserWithRolesAndPermissions):
                current_user = arg_value
                break
        
        if not current_user:
            raise AuthorizationError(detail="Usuario no autenticado")
        
        user_type = get_user_type(current_user)
        if user_type not in ["super_admin", "tenant_admin"]:
            raise AuthorizationError(
                detail="Se requieren privilegios de Administrador",
                internal_code="TENANT_ADMIN_REQUIRED_DECORATOR"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper

# 🎯 UTILIDADES ADICIONALES PARA DESARROLLO Y DEBUG
def get_user_permissions_summary(user: UserWithRolesAndPermissions) -> Dict[str, Any]:
    """
    Genera un resumen completo de permisos del usuario para debugging.
    
    Args:
        user: Usuario a analizar
        
    Returns:
        Dict: Resumen estructurado de permisos y roles
    """
    return {
        "usuario": user.nombre_usuario,
        "tipo_usuario": get_user_type(user),
        "roles": [rol.nombre for rol in user.roles],
        "permisos_directos": [perm.nombre for perm in user.permisos],
        "es_super_admin": get_user_type(user) == "super_admin",
        "es_tenant_admin": get_user_type(user) == "tenant_admin",
        "cliente_id": user.cliente.cliente_id if user.cliente else None
    }

def validate_permission_syntax(permission: str) -> bool:
    """
    Valida la sintaxis de un permiso (formato: modulo.accion).
    
    Args:
        permission: Permiso a validar
        
    Returns:
        bool: True si la sintaxis es válida
    """
    if not permission or '.' not in permission:
        return False
    
    modulo, accion = permission.split('.', 1)
    
    if not modulo.strip() or not accion.strip():
        return False
    
    # Validar caracteres permitidos
    import re
    if not re.match(r'^[a-z_]+$', modulo) or not re.match(r'^[a-z_]+$', accion):
        return False
    
    return True

# 🎯 INICIALIZACIÓN DEL SISTEMA DE AUTORIZACIÓN
def initialize_authorization_system():
    """
    Inicializa y valida el sistema de autorización al arrancar la aplicación.
    
    Realiza verificaciones de consistencia y configuración correcta.
    """
    logger.info("🔐 Inicializando sistema de autorización...")
    
    # Validar constantes de roles
    required_roles = [SUPER_ADMIN_ROLE, TENANT_ADMIN_ROLE]
    for role in required_roles:
        if not role or not isinstance(role, str):
            logger.error(f"Rol de autorización inválido: {role}")
            raise ValueError("Configuración de autorización inválida")
    
    # Validar estructura de permisos del sistema
    for modulo, acciones in PERMISOS_SISTEMA.items():
        if not modulo or not acciones:
            logger.error(f"Módulo o acciones inválidos en permisos del sistema: {modulo}")
            raise ValueError("Configuración de permisos del sistema inválida")
    
    logger.info("✅ Sistema de autorización inicializado correctamente")
    logger.info(f"📊 Permisos del sistema: {len(PERMISOS_SISTEMA)} módulos configurados")

# Ejecutar inicialización al importar el módulo
initialize_authorization_system()