#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de verificación de compatibilidad de Python.

Verifica que el sistema esté usando Python 3.12 y que todas las dependencias sean compatibles.
"""

import sys
import subprocess
import importlib.util
import os

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def verificar_version_python():
    """Verifica que sea Python 3.12."""
    version = sys.version_info
    print(f"Python detectado: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor == 12:
        print("[OK] Python 3.12 detectado - Compatible")
        return True
    elif version.major == 3 and version.minor == 13:
        print("[ADVERTENCIA] Python 3.13 detectado - Puede tener problemas con SQLAlchemy")
        print("   Recomendacion: Migrar a Python 3.12")
        return False
    elif version.major == 3 and version.minor >= 12:
        print("[OK] Python 3.12+ detectado - Compatible")
        return True
    else:
        print(f"[ERROR] Python {version.major}.{version.minor} detectado - No compatible")
        print("   Requerido: Python 3.12 o superior")
        return False

def verificar_sqlalchemy():
    """Verifica que SQLAlchemy esté instalado y funcione."""
    try:
        import sqlalchemy
        print(f"[OK] SQLAlchemy instalado: {sqlalchemy.__version__}")
        
        # Intentar importar componentes críticos
        from sqlalchemy import create_engine
        from sqlalchemy.pool import QueuePool
        print("[OK] SQLAlchemy importa correctamente")
        return True
    except AssertionError as e:
        if "TypingOnly" in str(e) or "SQLCoreOperations" in str(e):
            print("[ERROR] Error de compatibilidad SQLAlchemy + Python 3.13 detectado")
            print("   Solucion: Migrar a Python 3.12")
            return False
        else:
            print(f"[ERROR] Error en SQLAlchemy: {e}")
            return False
    except ImportError:
        print("[ERROR] SQLAlchemy no instalado")
        return False
    except Exception as e:
        print(f"[ADVERTENCIA] Advertencia en SQLAlchemy: {e}")
        return True

def verificar_dependencias():
    """Verifica dependencias críticas."""
    dependencias = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'pyodbc',
        'redis',
        'slowapi'
    ]
    
    print("\nVerificando dependencias:")
    todas_ok = True
    
    for dep in dependencias:
        try:
            mod = importlib.import_module(dep)
            version = getattr(mod, '__version__', 'N/A')
            print(f"  [OK] {dep}: {version}")
        except ImportError:
            print(f"  [ERROR] {dep}: No instalado")
            todas_ok = False
    
    return todas_ok

def verificar_entorno_virtual():
    """Verifica si está en un entorno virtual."""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print(f"[OK] Entorno virtual activo: {sys.prefix}")
    else:
        print("[ADVERTENCIA] No se detecta entorno virtual activo")
        print("   Recomendacion: Activar venv antes de ejecutar")
    
    return in_venv

def main():
    """Ejecuta todas las verificaciones."""
    print("=" * 60)
    print("VERIFICACION DE COMPATIBILIDAD DEL SISTEMA")
    print("=" * 60)
    
    resultados = []
    
    print("\n[1] Verificando version de Python:")
    resultados.append(("Python 3.12", verificar_version_python()))
    
    print("\n[2] Verificando entorno virtual:")
    resultados.append(("Entorno Virtual", verificar_entorno_virtual()))
    
    print("\n[3] Verificando SQLAlchemy:")
    resultados.append(("SQLAlchemy", verificar_sqlalchemy()))
    
    print("\n[4] Verificando dependencias:")
    resultados.append(("Dependencias", verificar_dependencias()))
    
    print("\n" + "=" * 60)
    print("RESUMEN:")
    print("=" * 60)
    
    todo_ok = True
    for nombre, resultado in resultados:
        estado = "[OK]" if resultado else "[FALLO]"
        print(f"  {estado} - {nombre}")
        if not resultado:
            todo_ok = False
    
    print("\n" + "=" * 60)
    if todo_ok:
        print("[OK] Sistema listo para usar")
    else:
        print("[ADVERTENCIA] Hay problemas que resolver")
        print("\nVer guia: GUIA_MIGRACION_PYTHON312.md")
    print("=" * 60)
    
    return 0 if todo_ok else 1

if __name__ == "__main__":
    sys.exit(main())

