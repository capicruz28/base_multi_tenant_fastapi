#!/usr/bin/env python3
"""
Script para analizar código legacy y identificar qué necesita migración.

✅ FASE 3: MANTENIBILIDAD - Análisis de código legacy
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
APP_DIR = PROJECT_ROOT / "app"

# Patrones a buscar
DEPRECATED_IMPORTS = [
    r'from app\.infrastructure\.database\.queries import',
    r'from app\.db\.queries import',
]

SYNC_EXECUTE_PATTERNS = [
    r'execute_query\s*\([^)]*\)\s*(?!\s*await)',  # execute_query sin await
    r'execute_insert\s*\([^)]*\)\s*(?!\s*await)',
    r'execute_update\s*\([^)]*\)\s*(?!\s*await)',
    r'execute_auth_query\s*\([^)]*\)\s*(?!\s*await)',
]

ASYNC_EXECUTE_PATTERNS = [
    r'await\s+execute_query\s*\(',
    r'await\s+execute_insert\s*\(',
    r'await\s+execute_update\s*\(',
    r'await\s+execute_auth_query\s*\(',
]

RAW_SQL_PATTERNS = [
    r'query\s*=\s*["\'].*SELECT.*FROM',
    r'query\s*=\s*f["\'].*SELECT.*FROM',
]


def find_python_files(directory: Path) -> List[Path]:
    """Encuentra todos los archivos Python."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'node_modules', 'tests']]
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    return python_files


def analyze_file(file_path: Path) -> Dict:
    """Analiza un archivo en busca de código legacy."""
    issues = {
        'deprecated_imports': [],
        'sync_executes': [],
        'async_executes': [],
        'raw_sql': [],
        'needs_migration': False
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Buscar imports deprecated
        for line_num, line in enumerate(lines, 1):
            for pattern in DEPRECATED_IMPORTS:
                if re.search(pattern, line):
                    issues['deprecated_imports'].append({
                        'line': line_num,
                        'content': line.strip()
                    })
                    issues['needs_migration'] = True
        
        # Buscar execute_query sin await
        for line_num, line in enumerate(lines, 1):
            for pattern in SYNC_EXECUTE_PATTERNS:
                if re.search(pattern, line):
                    issues['sync_executes'].append({
                        'line': line_num,
                        'content': line.strip()
                    })
                    issues['needs_migration'] = True
        
        # Contar async executes (bueno)
        for line_num, line in enumerate(lines, 1):
            for pattern in ASYNC_EXECUTE_PATTERNS:
                if re.search(pattern, line):
                    issues['async_executes'].append({
                        'line': line_num,
                        'content': line.strip()
                    })
        
        # Buscar raw SQL (advertencia)
        for line_num, line in enumerate(lines, 1):
            for pattern in RAW_SQL_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE | re.DOTALL):
                    issues['raw_sql'].append({
                        'line': line_num,
                        'content': line.strip()[:100]
                    })
    
    except Exception as e:
        print(f"Error analizando {file_path}: {e}")
    
    return issues


def main():
    """Función principal."""
    print("Analizando codigo legacy...")
    print(f"Directorio: {APP_DIR}\n")
    
    python_files = find_python_files(APP_DIR)
    print(f"Archivos Python encontrados: {len(python_files)}\n")
    
    all_issues = {}
    files_needing_migration = []
    
    for file_path in python_files:
        relative_path = str(file_path.relative_to(PROJECT_ROOT))
        issues = analyze_file(file_path)
        
        if issues['needs_migration'] or issues['raw_sql']:
            all_issues[relative_path] = issues
            if issues['needs_migration']:
                files_needing_migration.append(relative_path)
    
    # Reporte
    print("=" * 80)
    print("REPORTE DE ANALISIS DE CODIGO LEGACY")
    print("=" * 80)
    print(f"\n[CRITICO] Archivos que necesitan migracion: {len(files_needing_migration)}")
    print(f"[ADVERTENCIA] Archivos con raw SQL: {len([f for f, i in all_issues.items() if i['raw_sql']])}")
    print(f"[OK] Archivos usando async correctamente: {len([f for f, i in all_issues.items() if i['async_executes']])}\n")
    
    if files_needing_migration:
        print("\n" + "=" * 80)
        print("[CRITICO] ARCHIVOS QUE NECESITAN MIGRACION")
        print("=" * 80)
        for file_path in sorted(files_needing_migration):
            issues = all_issues[file_path]
            print(f"\n[ARCHIVO] {file_path}")
            
            if issues['deprecated_imports']:
                print(f"   [WARN] Imports deprecated ({len(issues['deprecated_imports'])}):")
                for imp in issues['deprecated_imports'][:3]:
                    print(f"      L{imp['line']}: {imp['content']}")
            
            if issues['sync_executes']:
                print(f"   [WARN] Ejecuciones sincronas ({len(issues['sync_executes'])}):")
                for exec in issues['sync_executes'][:3]:
                    print(f"      L{exec['line']}: {exec['content']}")
    
    # Resumen de raw SQL
    raw_sql_files = {f: i for f, i in all_issues.items() if i['raw_sql']}
    if raw_sql_files:
        print("\n" + "=" * 80)
        print("[ADVERTENCIA] ARCHIVOS CON RAW SQL (considerar migrar a SQLAlchemy Core)")
        print("=" * 80)
        for file_path in sorted(raw_sql_files.keys())[:10]:
            issues = raw_sql_files[file_path]
            print(f"\n[ARCHIVO] {file_path}")
            print(f"   Raw SQL encontrado: {len(issues['raw_sql'])} lugares")
    
    print("\n" + "=" * 80)
    print("[OK] Analisis completado")
    print("=" * 80)
    
    return 0 if not files_needing_migration else 1


if __name__ == "__main__":
    exit(main())

