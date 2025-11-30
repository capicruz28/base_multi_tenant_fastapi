# tests/conftest.py
"""
Configuración compartida para tests (pytest fixtures).

✅ NUEVO: Fixtures comunes para todos los tests
"""

import pytest
from typing import Generator
from unittest.mock import Mock, MagicMock

# Configuración de pytest
pytest_plugins = []


@pytest.fixture
def mock_db_connection():
    """Mock de conexión a base de datos."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None
    return mock_conn


@pytest.fixture
def mock_tenant_context():
    """Mock de contexto de tenant."""
    from unittest.mock import patch
    with patch('app.core.tenant.context.get_current_client_id', return_value=1):
        yield


@pytest.fixture
def sample_usuario_data():
    """Datos de ejemplo para usuario."""
    return {
        'usuario_id': 1,
        'nombre_usuario': 'test_user',
        'email': 'test@example.com',
        'cliente_id': 1,
        'es_activo': True,
        'es_superadmin': False,
        'roles': []
    }


@pytest.fixture
def sample_cliente_data():
    """Datos de ejemplo para cliente."""
    return {
        'cliente_id': 1,
        'nombre': 'Cliente Test',
        'subdominio': 'test',
        'es_activo': True
    }

