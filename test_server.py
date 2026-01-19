#!/usr/bin/env python3
"""
Script de prueba para verificar que el servidor puede iniciarse.
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Verificando imports y configuracion...")

try:
    # Verificar que los imports funcionan
    from app.main import app
    print("[OK] Aplicacion importada correctamente")
    
    # Verificar que la app tiene las rutas básicas
    routes = [route.path for route in app.routes]
    print(f"[OK] Rutas encontradas: {len(routes)}")
    
    # Verificar rutas importantes
    important_routes = ["/", "/health", "/docs", "/api/v1"]
    found_routes = [r for r in important_routes if any(r in route.path for route in app.routes)]
    print(f"[OK] Rutas importantes: {found_routes}")
    
    print("\n[OK] SERVIDOR LISTO PARA EJECUTAR")
    print("\nPara iniciar el servidor, ejecuta:")
    print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    print("\nO simplemente:")
    print("  python app/main.py")
    print("\n[NOTA] Asegurate de tener configuradas las variables de entorno")
    print("   (DB_SERVER, DB_USER, DB_PASSWORD, etc.) en un archivo .env")
    
except ImportError as e:
    print(f"[ERROR] Error de importacion: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

