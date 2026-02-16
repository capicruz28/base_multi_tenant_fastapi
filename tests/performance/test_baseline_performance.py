"""
Tests de baseline de performance.

✅ FASE 0: Tests creados para medir performance antes/después de refactorización
✅ Usar para detectar degradación de performance

OBJETIVO:
- Establecer baseline de performance
- Detectar regresiones de performance
- Validar mejoras de performance
"""

import pytest
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestBaselinePerformance:
    """
    Suite de tests de performance baseline.
    
    ⚠️ Estos tests son informativos, no bloqueantes.
    """
    
    def test_endpoint_response_time_baseline(self):
        """Medir tiempo de respuesta de endpoints básicos."""
        endpoints = [
            "/health",
            "/docs",
            "/openapi.json"
        ]
        
        max_response_time = 2.0  # 2 segundos máximo
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            elapsed_time = time.time() - start_time
            
            # No fallar si endpoint no existe, solo medir si existe
            if response.status_code != 404:
                assert elapsed_time < max_response_time, (
                    f"Endpoint {endpoint} tardó {elapsed_time:.2f}s "
                    f"(máximo permitido: {max_response_time}s)"
                )
                print(f"✅ {endpoint}: {elapsed_time:.3f}s")
    
    def test_import_performance(self):
        """Medir tiempo de importación de módulos críticos."""
        import_times = {}
        
        modules = [
            "app.infrastructure.database.sql_constants",
            "app.infrastructure.database.queries_async",
            "app.infrastructure.database.connection_async",
            "app.core.tenant.context",
        ]
        
        for module_name in modules:
            start_time = time.time()
            __import__(module_name)
            elapsed_time = time.time() - start_time
            import_times[module_name] = elapsed_time
            print(f"✅ Import {module_name}: {elapsed_time:.3f}s")
        
        # Validar que imports no son excesivamente lentos
        max_import_time = 1.0  # 1 segundo máximo por import
        for module, elapsed in import_times.items():
            assert elapsed < max_import_time, (
                f"Import de {module} tardó {elapsed:.2f}s "
                f"(máximo permitido: {max_import_time}s)"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
