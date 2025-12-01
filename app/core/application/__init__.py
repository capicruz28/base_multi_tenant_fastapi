# app/core/application/__init__.py
"""
Core Application Layer: Utilidades compartidas para la capa de aplicación.

Esta carpeta contiene clases base y utilidades que pueden ser usadas por
todos los servicios de aplicación en los diferentes módulos.

✅ ARQUITECTURA: Corrige la violación de capas moviendo BaseService
de infrastructure a core/application, donde pertenece según DDD.
"""

from app.core.application.base_service import BaseService

__all__ = ['BaseService']

