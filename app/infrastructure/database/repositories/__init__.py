# app/infrastructure/database/repositories/__init__.py
"""
Repositorios: Abstracción de acceso a datos.

✅ FASE 3: ARQUITECTURA - Completar capa de repositorios
"""

from app.infrastructure.database.repositories.base_service import BaseService
from app.infrastructure.database.repositories.base_repository import BaseRepository

__all__ = ['BaseService', 'BaseRepository']

