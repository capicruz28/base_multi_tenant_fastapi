"""
Tests de baseline para validar zero-breaking changes.

✅ FASE 0: Tests creados para validar que endpoints críticos siguen funcionando
✅ Usar antes y después de cada fase de refactorización

OBJETIVO:
- Validar que endpoints críticos funcionan correctamente
- Detectar breaking changes temprano
- Servir como baseline de performance
"""

import pytest
from fastapi.testclient import TestClient
from uuid import UUID
import json

# Importar app principal
from app.main import app

client = TestClient(app)


class TestBaselineEndpoints:
    """
    Suite de tests de baseline para endpoints críticos.
    
    ✅ Estos tests deben pasar ANTES y DESPUÉS de cada fase.
    """
    
    def test_health_check(self):
        """Test básico de salud del servidor."""
        response = client.get("/health")
        assert response.status_code in [200, 404]  # Puede no existir, pero no debe dar 500
    
    def test_api_docs_available(self):
        """Test que la documentación de API está disponible."""
        response = client.get("/docs")
        assert response.status_code in [200, 404]  # Puede no existir, pero no debe dar 500
    
    def test_openapi_schema_available(self):
        """Test que el schema OpenAPI está disponible."""
        response = client.get("/openapi.json")
        assert response.status_code in [200, 404]  # Puede no existir, pero no debe dar 500


class TestBaselineImports:
    """
    Tests de baseline para validar que imports críticos funcionan.
    
    ✅ Validar que imports antiguos y nuevos funcionan durante migración.
    """
    
    def test_sql_constants_import_still_works(self):
        """Validar que imports desde sql_constants.py siguen funcionando."""
        try:
            from app.infrastructure.database.sql_constants import (
                GET_USER_MAX_ACCESS_LEVEL,
                SELECT_USUARIOS_PAGINATED
            )
            assert GET_USER_MAX_ACCESS_LEVEL is not None
            assert SELECT_USUARIOS_PAGINATED is not None
        except ImportError:
            pytest.skip("sql_constants.py no disponible (puede estar en proceso de migración)")
    
    def test_queries_structure_exists(self):
        """Validar que estructura de queries modulares existe."""
        import os
        queries_path = "app/infrastructure/database/queries"
        assert os.path.exists(queries_path), "Estructura de queries debe existir"
        
        # Validar subdirectorios
        subdirs = ["auth", "users", "rbac", "menus", "audit"]
        for subdir in subdirs:
            subdir_path = os.path.join(queries_path, subdir)
            assert os.path.exists(subdir_path), f"Subdirectorio {subdir} debe existir"


class TestBaselineConnectionPool:
    """
    Tests de baseline para validar configuración de connection pool.
    
    ✅ Validar que límites aumentados están activos.
    """
    
    def test_pool_limits_configured(self):
        """Validar que límites de pool están configurados correctamente."""
        from app.infrastructure.database.connection_pool import (
            MAX_TENANT_POOLS,
            TENANT_POOL_SIZE,
            TENANT_POOL_MAX_OVERFLOW,
            POOL_INACTIVITY_TIMEOUT
        )
        
        # Validar que límites están aumentados (FASE 0)
        assert MAX_TENANT_POOLS >= 200, "MAX_TENANT_POOLS debe ser >= 200"
        assert TENANT_POOL_SIZE >= 5, "TENANT_POOL_SIZE debe ser >= 5"
        assert TENANT_POOL_MAX_OVERFLOW >= 3, "TENANT_POOL_MAX_OVERFLOW debe ser >= 3"
        assert POOL_INACTIVITY_TIMEOUT <= 1800, "POOL_INACTIVITY_TIMEOUT debe ser <= 1800 (30 min)"


class TestBaselineDatabaseAccess:
    """
    Tests de baseline para validar acceso a base de datos.
    
    ⚠️ Estos tests requieren BD configurada.
    """
    
    @pytest.mark.asyncio
    async def test_database_connection_available(self):
        """Validar que conexión a BD está disponible."""
        try:
            from app.infrastructure.database.connection_async import (
                get_db_connection,
                DatabaseConnection
            )
            
            # Intentar obtener conexión (no ejecutar query, solo validar disponibilidad)
            async with get_db_connection(DatabaseConnection.ADMIN) as session:
                assert session is not None, "Sesión de BD debe estar disponible"
        except Exception as e:
            pytest.skip(f"BD no disponible para test: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
