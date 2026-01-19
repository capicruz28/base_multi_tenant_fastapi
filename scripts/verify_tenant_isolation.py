#!/usr/bin/env python3
"""
Script de verificación de aislamiento multi-tenant.

✅ FASE 1 SEGURIDAD: Verifica que todas las queries incluyan filtro de tenant.

Uso:
    python scripts/verify_tenant_isolation.py
"""

import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
APP_DIR = PROJECT_ROOT / "app"

# Patrones para detectar queries
EXECUTE_QUERY_PATTERN = re.compile(r'execute_query\s*\(')
SKIP_TENANT_PATTERN = re.compile(r'skip_tenant_validation\s*=\s*True')
CLIENT_ID_PATTERN = re.compile(r'client_id\s*=')

# Tablas globales que no requieren filtro
GLOBAL_TABLES = {
    'cliente', 'cliente_modulo', 'cliente_conexion', 
    'sistema_config', 'cliente_modulo_activo'
}


def find_python_files(directory: Path) -> List[Path]:
    """Encuentra todos los archivos Python en el directorio."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Ignorar directorios comunes
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files


def analyze_file(file_path: Path) -> List[Dict]:
    """Analiza un archivo Python en busca de queries sin filtro de tenant."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Buscar llamadas a execute_query
        for line_num, line in enumerate(lines, 1):
            if EXECUTE_QUERY_PATTERN.search(line):
                # Verificar si tiene skip_tenant_validation=True
                if SKIP_TENANT_PATTERN.search(line):
                    # Buscar contexto (líneas alrededor)
                    context_start = max(0, line_num - 3)
                    context_end = min(len(lines), line_num + 3)
                    context = '\n'.join(lines[context_start:context_end])
                    
                    issues.append({
                        'file': str(file_path.relative_to(PROJECT_ROOT)),
                        'line': line_num,
                        'type': 'skip_tenant_validation',
                        'severity': 'HIGH',
                        'message': 'Uso de skip_tenant_validation=True detectado',
                        'context': context
                    })
                
                # Verificar si tiene client_id en los parámetros
                # (búsqueda simple, puede tener falsos positivos)
                if not CLIENT_ID_PATTERN.search(line):
                    # Verificar si es una query a tabla global
                    is_global_table = False
                    for table in GLOBAL_TABLES:
                        if table in line.lower():
                            is_global_table = True
                            break
                    
                    if not is_global_table:
                        # Buscar en líneas siguientes (puede estar en múltiples líneas)
                        next_lines = '\n'.join(lines[line_num:min(len(lines), line_num + 5)])
                        if not CLIENT_ID_PATTERN.search(next_lines):
                            context_start = max(0, line_num - 2)
                            context_end = min(len(lines), line_num + 5)
                            context = '\n'.join(lines[context_start:context_end])
                            
                            issues.append({
                                'file': str(file_path.relative_to(PROJECT_ROOT)),
                                'line': line_num,
                                'type': 'missing_client_id',
                                'severity': 'MEDIUM',
                                'message': 'Posible query sin client_id explícito',
                                'context': context
                            })
    
    except Exception as e:
        print(f"Error analizando {file_path}: {e}")
    
    return issues


def main():
    """Función principal del script."""
    print("🔍 Verificando aislamiento multi-tenant...")
    print(f"📁 Directorio: {APP_DIR}\n")
    
    python_files = find_python_files(APP_DIR)
    print(f"📄 Archivos Python encontrados: {len(python_files)}\n")
    
    all_issues = []
    for file_path in python_files:
        issues = analyze_file(file_path)
        all_issues.extend(issues)
    
    # Agrupar por tipo
    skip_issues = [i for i in all_issues if i['type'] == 'skip_tenant_validation']
    missing_client_id_issues = [i for i in all_issues if i['type'] == 'missing_client_id']
    
    # Reporte
    print("=" * 80)
    print("📊 REPORTE DE VERIFICACIÓN")
    print("=" * 80)
    print(f"\n🔴 CRÍTICO: skip_tenant_validation=True encontrado: {len(skip_issues)}")
    print(f"🟡 ADVERTENCIA: Posibles queries sin client_id: {len(missing_client_id_issues)}")
    print(f"📝 Total de issues: {len(all_issues)}\n")
    
    if skip_issues:
        print("\n" + "=" * 80)
        print("🔴 ISSUES CRÍTICOS (skip_tenant_validation=True)")
        print("=" * 80)
        for issue in skip_issues:
            print(f"\n📄 {issue['file']}:{issue['line']}")
            print(f"   {issue['message']}")
            print(f"   Contexto:")
            for ctx_line in issue['context'].split('\n'):
                print(f"   {ctx_line}")
    
    if missing_client_id_issues:
        print("\n" + "=" * 80)
        print("🟡 ADVERTENCIAS (posibles queries sin client_id)")
        print("=" * 80)
        # Mostrar solo los primeros 10
        for issue in missing_client_id_issues[:10]:
            print(f"\n📄 {issue['file']}:{issue['line']}")
            print(f"   {issue['message']}")
            print(f"   Contexto:")
            for ctx_line in issue['context'].split('\n')[:3]:
                print(f"   {ctx_line}")
        
        if len(missing_client_id_issues) > 10:
            print(f"\n   ... y {len(missing_client_id_issues) - 10} más")
    
    print("\n" + "=" * 80)
    if len(all_issues) == 0:
        print("✅ No se encontraron issues críticos")
        return 0
    else:
        print(f"⚠️  Se encontraron {len(all_issues)} issues")
        print("\n💡 RECOMENDACIONES:")
        print("   1. Revisar manualmente cada issue")
        print("   2. Verificar que las queries usen SQLAlchemy Core con apply_tenant_filter")
        print("   3. Asegurar que todas las queries incluyan filtro de cliente_id")
        return 1


if __name__ == "__main__":
    exit(main())


