"""
Configuración global de pytest.

✅ FASE 3: MANTENIBILIDAD - Configuración de tests
"""

import pytest
import asyncio
from uuid import uuid4
from unittest.mock import patch

from app.core.tenant.context import TenantContext, set_tenant_context, reset_tenant_context


@pytest.fixture
def event_loop():
    """Crear event loop para tests async."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_tenant_context():
    """Contexto de tenant de ejemplo para tests."""
    return TenantContext(
        client_id=uuid4(),
        subdominio="test",
        codigo_cliente="TEST",
        database_type="single",
        nombre_bd="test_db",
        servidor="localhost",
        puerto=1433
    )


@pytest.fixture
def mock_tenant_context(sample_tenant_context):
    """Fixture que establece contexto de tenant para tests."""
    tokens = set_tenant_context(sample_tenant_context)
    yield sample_tenant_context
    reset_tenant_context(tokens)


@pytest.fixture
def mock_settings():
    """Fixture para mockear settings."""
    with patch('app.core.config.settings') as mock:
        # Valores por defecto seguros
        mock.ENABLE_QUERY_TENANT_VALIDATION = True
        mock.ALLOW_TENANT_FILTER_BYPASS = False
        mock.ENVIRONMENT = "test"
        mock.ENABLE_CONNECTION_POOLING = False
        mock.ENABLE_REDIS_CACHE = False
        yield mock
