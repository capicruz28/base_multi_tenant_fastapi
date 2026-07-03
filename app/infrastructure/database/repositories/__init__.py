# app/infrastructure/database/repositories/__init__.py
"""
Repositorios: Abstracción de acceso a datos.

✅ FASE 3: ARQUITECTURA - Completar capa de repositorios
"""

# ✅ ARQUITECTURA: BaseService movido a app/core/application/base_service.py
# Mantenemos re-exportación para compatibilidad con código existente
from app.core.application.base_service import BaseService
from app.infrastructure.database.repositories.base_repository import BaseRepository
from app.infrastructure.database.repositories.cfg_codigo_secuencia_repository import (
    CfgCodigoSecuenciaRepository,
)

from app.infrastructure.database.repositories.tenant_provisioning_repository import (
    TenantProvisioningRepository,
)

__all__ = ['BaseService', 'BaseRepository', 'CfgCodigoSecuenciaRepository', 'TenantProvisioningRepository']

