#!/usr/bin/env python3
"""
Script de validación: Ejecuta tests de baseline y valida que todo funcione.

✅ Usar antes y después de cada fase para validar zero-breaking changes.
"""

import subprocess
import sys
import json
from pathlib import Path

def run_tests(test_path: str = "tests/integration") -> dict:
    """
    Ejecuta tests y retorna resultados.
    
    Returns:
        Dict con resultados de tests
    """
    print(f"🧪 Ejecutando tests en {test_path}...")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            ["pytest", test_path, "-v", "--tb=short", "--json-report", "--json-report-file=test_results.json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Leer resultados JSON si existe
        results = {}
        if Path("test_results.json").exists():
            with open("test_results.json") as f:
                results = json.load(f)
        
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "results": results
        }
    except FileNotFoundError:
        print("❌ pytest no encontrado. Instalar con: pip install pytest pytest-json-report")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error ejecutando tests: {e}")
        sys.exit(1)


def validate_baseline():
    """Valida que los tests de baseline pasen."""
    print("=" * 60)
    print("📊 VALIDACIÓN DE BASELINE")
    print("=" * 60)
    print()
    
    # Ejecutar tests de integración
    test_results = run_tests("tests/integration")
    
    # Ejecutar tests de endpoints críticos
    endpoint_results = run_tests("tests/integration/test_baseline_endpoints.py")
    
    # Analizar resultados
    all_passed = (
        test_results["returncode"] == 0 and
        endpoint_results["returncode"] == 0
    )
    
    if all_passed:
        print()
        print("=" * 60)
        print("✅ VALIDACIÓN EXITOSA")
        print("=" * 60)
        print("✅ Todos los tests de baseline pasaron")
        print("✅ Zero breaking changes confirmado")
        return True
    else:
        print()
        print("=" * 60)
        print("❌ VALIDACIÓN FALLIDA")
        print("=" * 60)
        print("❌ Algunos tests fallaron")
        print()
        print("STDOUT:")
        print(test_results["stdout"])
        print()
        print("STDERR:")
        print(test_results["stderr"])
        return False


if __name__ == "__main__":
    success = validate_baseline()
    sys.exit(0 if success else 1)
