# app/infrastructure/redis/__init__.py
"""
Módulo de infraestructura Redis para servicios asíncronos.
"""

from app.infrastructure.redis.client import RedisService

__all__ = ["RedisService"]


