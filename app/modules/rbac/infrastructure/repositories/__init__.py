# app/modules/rbac/infrastructure/repositories/__init__.py
"""
Repositorios del módulo RBAC.
"""

from app.modules.rbac.infrastructure.repositories.rol_repository import RolRepository
from app.modules.rbac.infrastructure.repositories.permiso_repository import PermisoRepository

__all__ = ['RolRepository', 'PermisoRepository']

