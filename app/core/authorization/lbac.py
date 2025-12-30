"""
Sistema de autorización por niveles de acceso
Decoradores para validar permisos basados en niveles LBAC
"""

from functools import wraps
from typing import Optional, Any
from fastapi import HTTPException, status, Depends

from app.api.deps import get_current_active_user


class InsufficientAccessLevelError(HTTPException):
    """Excepción para nivel de acceso insuficiente"""
    def __init__(self, required_level: int, current_level: int):
        detail = f"Nivel de acceso insuficiente. Requerido: {required_level}, Actual: {current_level}"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class SuperAdminRequiredError(HTTPException):
    """Excepción para cuando se requiere ser super admin"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de Super Administrador para esta operación"
        )


class TenantAccessError(HTTPException):
    """Excepción para acceso a tenant no autorizado"""
    def __init__(self, target_cliente_id: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tiene permisos para acceder al cliente ID: {target_cliente_id}"
        )


def require_access_level(min_level: int):
    """
    Decorador para validar nivel mínimo de acceso requerido
    
    Args:
        min_level (int): Nivel mínimo requerido (1-5)
    
    Returns:
        function: Decorador que valida el nivel de acceso
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obtener el usuario actual del contexto
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no autenticado"
                )
            
            # Validar nivel de acceso
            user_access_level = getattr(current_user, 'access_level', 1)
            if user_access_level < min_level:
                raise InsufficientAccessLevelError(min_level, user_access_level)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_super_admin():
    """
    Decorador para validar que el usuario es Super Admin (nivel 5)
    
    Returns:
        function: Decorador que valida rol de super admin
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Buscar current_user en kwargs o en args
            current_user = kwargs.get('current_user')
            
            # Si no está en kwargs, buscar en args (puede venir como parámetro posicional)
            if not current_user:
                for arg in args:
                    if hasattr(arg, 'is_super_admin') or hasattr(arg, 'nombre_usuario'):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no autenticado"
                )
            
            # Validar si es super admin - verificar tanto is_super_admin como access_level
            is_super_admin = getattr(current_user, 'is_super_admin', False)
            access_level = getattr(current_user, 'access_level', 0)
            
            # También verificar si tiene el rol SuperAdministrador
            has_super_admin_role = False
            if hasattr(current_user, 'roles'):
                from app.core.authorization.rbac import SUPER_ADMIN_ROLE
                has_super_admin_role = any(
                    rol.nombre == SUPER_ADMIN_ROLE for rol in current_user.roles
                )
            
            if not (is_super_admin or access_level >= 5 or has_super_admin_role):
                raise SuperAdminRequiredError()
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator




def require_tenant_admin():
    """
    Decorador para validar que el usuario es al menos Tenant Admin (nivel >= 4)
    
    Returns:
        function: Decorador que valida rol de tenant admin
    """
    return require_access_level(4)


def validate_user_level(user, required_level: int) -> bool:
    """
    Función helper para validar nivel de usuario
    
    Args:
        user: Objeto usuario con access_level
        required_level (int): Nivel requerido
    
    Returns:
        bool: True si cumple con el nivel requerido
    """
    user_access_level = getattr(user, 'access_level', 1)
    return user_access_level >= required_level


def validate_tenant_access(current_user, target_cliente_id: int) -> bool:
    """
    Validar que un tenant admin solo pueda acceder a su propio cliente
    
    Args:
        current_user: Usuario actual
        target_cliente_id (int): ID del cliente objetivo
    
    Returns:
        bool: True si tiene acceso al cliente
    """
    # Super admin puede acceder a cualquier cliente
    if getattr(current_user, 'is_super_admin', False):
        return True
    
    # Tenant admin solo puede acceder a su propio cliente
    user_cliente_id = getattr(current_user, 'cliente_id', None)
    return user_cliente_id == target_cliente_id


# Alias para compatibilidad
require_admin = require_tenant_admin
require_min_level = require_access_level