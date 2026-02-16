#!/usr/bin/env python3
"""
Script de validación: Verifica que no haya imports de sql_constants.py

✅ FASE 2: Usar antes de eliminar sql_constants.py
"""

import ast
import os
import sys
from pathlib import Path

def find_sql_constants_imports(root_dir: str = "app") -> list:
    """
    Busca imports de sql_constants.py en todo el código.
    
    Returns:
        Lista de archivos que importan sql_constants.py
    """
    imports_found = []
    
    for root, dirs, files in os.walk(root_dir):
        # Excluir directorios que no son código
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]
        
        for file in files:
            if not file.endswith(".py"):
                continue
            
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Buscar imports de sql_constants
                    if "sql_constants" in content:
                        # Verificar que no sea solo un comentario
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if "sql_constants" in line and not line.strip().startswith('#'):
                                imports_found.append({
                                    "file": file_path,
                                    "line": i,
                                    "content": line.strip()
                                })
                                break  # Solo reportar una vez por archivo
            except Exception as e:
                print(f"⚠️  Error leyendo {file_path}: {e}", file=sys.stderr)
    
    return imports_found


def main():
    """Ejecuta validación."""
    print("Buscando imports de sql_constants.py...")
    print("-" * 60)
    
    imports = find_sql_constants_imports()
    
    if imports:
        print(f"[WARNING] Se encontraron {len(imports)} archivo(s) con imports de sql_constants.py:\n")
        for imp in imports:
            print(f"  - {imp['file']}:{imp['line']}")
            print(f"    {imp['content']}")
            print()
        
        print("\n[INFO] NOTA: Estos imports siguen funcionando gracias a re-exports.")
        print("   Migrar gradualmente a estructura modular cuando sea conveniente.")
        print("   Ver: docs/MIGRACION_QUERIES.md")
        print("\n[INFO] sql_constants.py se mantendrá con re-exports por compatibilidad.")
        
        sys.exit(0)  # No es error, solo información
    else:
        print("[OK] No se encontraron imports de sql_constants.py")
        print("[OK] Es seguro eliminar sql_constants.py")
        sys.exit(0)


if __name__ == "__main__":
    main()
