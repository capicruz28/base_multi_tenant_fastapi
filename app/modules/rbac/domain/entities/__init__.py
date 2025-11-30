# app/modules/rbac/domain/entities/__init__.py
"""
Entidades de dominio del módulo RBAC.
"""

from app.modules.rbac.domain.entities.rol import Rol
from app.modules.rbac.domain.entities.permiso import Permiso

__all__ = ['Rol', 'Permiso']

