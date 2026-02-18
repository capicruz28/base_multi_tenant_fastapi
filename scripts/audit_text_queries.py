#!/usr/bin/env python3
"""
Script para auditar queries que usan text() o string SQL.
Identifica queries que tocan tablas con cliente_id sin filtro explícito.

✅ FASE 2: Auditoría automática de queries TextClause/String
"""

import re
import ast
from pathlib import Path
from typing import List, Dict, Set
import json

# Tablas que requieren filtro de cliente_id
TABLAS_CON_CLIENTE_ID = {
    'usuario', 'rol', 'usuario_rol', 'rol_menu_permiso',
    'refresh_tokens', 'auth_audit_log', 'log_sincronizacion_usuario'
}

# Tablas globales que NO requieren filtro de tenant
TABLAS_GLOBALES = {
    'cliente', 'cliente_modulo', 'cliente_conexion', 'sistema_config',
    'modulo', 'modulo_seccion', 'modulo_menu', 'modulo_rol_plantilla'
}

def find_text_queries_in_file(file_path: Path) -> List[Dict]:
    """
    Encuentra queries que usan text() o string SQL en un archivo.
    
    Returns:
        Lista de diccionarios con información de cada query encontrada
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return [{
            'file': str(file_path),
            'line': 0,
            'issue': f'Error leyendo archivo: {e}',
            'severity': 'error'
        }]
    
    # Buscar patrones de text() o queries SQL directas
    for i, line in enumerate(lines, 1):
        # Buscar text( o TextClause
        if 'text(' in line.lower() or 'textclause' in line.lower():
            # Buscar contexto (próximas 20 líneas para ver la query completa)
            context_start = max(0, i - 2)
            context_end = min(len(lines), i + 20)
            context = '\n'.join(lines[context_start:context_end])
            
            # Verificar si toca tablas con cliente_id
            for tabla in TABLAS_CON_CLIENTE_ID:
                if tabla in context.lower():
                    # Verificar si tiene cliente_id en la query
                    context_lower = context.lower()
                    has_cliente_id = (
                        'cliente_id' in context_lower or
                        'client_id' in context_lower
                    )
                    
                    if not has_cliente_id:
                        issues.append({
                            'file': str(file_path),
                            'line': i,
                            'issue': f'Query con text() toca tabla {tabla} sin cliente_id visible',
                            'severity': 'high',
                            'tabla': tabla,
                            'context': context[:500],
                            'type': 'text()'
                        })
                    else:
                        # Tiene cliente_id, pero verificar que se use correctamente
                        issues.append({
                            'file': str(file_path),
                            'line': i,
                            'issue': f'Query con text() toca tabla {tabla} (verificar uso de cliente_id)',
                            'severity': 'medium',
                            'tabla': tabla,
                            'context': context[:500],
                            'type': 'text() - tiene cliente_id'
                        })
        
        # Buscar queries SQL directas (strings con SELECT, UPDATE, DELETE, INSERT)
        sql_keywords = ['select', 'update', 'delete', 'insert']
        if any(keyword in line.lower() for keyword in sql_keywords):
            # Verificar si es una query SQL directa (no comentario)
            if not line.strip().startswith('#') and not line.strip().startswith('"""'):
                # Buscar contexto
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 10)
                context = '\n'.join(lines[context_start:context_end])
                
                # Verificar si toca tablas con cliente_id
                for tabla in TABLAS_CON_CLIENTE_ID:
                    if tabla in context.lower():
                        context_lower = context.lower()
                        has_cliente_id = (
                            'cliente_id' in context_lower or
                            'client_id' in context_lower
                        )
                        
                        if not has_cliente_id:
                            issues.append({
                                'file': str(file_path),
                                'line': i,
                                'issue': f'Query SQL directa toca tabla {tabla} sin cliente_id visible',
                                'severity': 'high',
                                'tabla': tabla,
                                'context': context[:500],
                                'type': 'sql_string'
                            })
    
    return issues


def audit_directory(directory: Path) -> List[Dict]:
    """
    Audita todos los archivos Python en un directorio.
    
    Args:
        directory: Directorio a auditar
    
    Returns:
        Lista de todos los issues encontrados
    """
    all_issues = []
    
    # Buscar todos los archivos Python
    for py_file in directory.rglob('*.py'):
        # Excluir archivos de test y migraciones por ahora
        if 'test' in str(py_file) or 'migration' in str(py_file) or '__pycache__' in str(py_file):
            continue
        
        issues = find_text_queries_in_file(py_file)
        all_issues.extend(issues)
    
    return all_issues


def generate_report(issues: List[Dict], output_file: Path = None) -> str:
    """
    Genera un reporte de los issues encontrados.
    
    Args:
        issues: Lista de issues encontrados
        output_file: Archivo donde guardar el reporte (opcional)
    
    Returns:
        String con el reporte formateado
    """
    # Agrupar por severidad
    high_severity = [i for i in issues if i.get('severity') == 'high']
    medium_severity = [i for i in issues if i.get('severity') == 'medium']
    
    # Agrupar por archivo
    by_file = {}
    for issue in issues:
        file_path = issue['file']
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(issue)
    
    # Generar reporte
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("AUDITORÍA DE QUERIES TEXTCLAUSE/STRING")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"Total de issues encontrados: {len(issues)}")
    report_lines.append(f"  - Alta severidad: {len(high_severity)}")
    report_lines.append(f"  - Media severidad: {len(medium_severity)}")
    report_lines.append("")
    
    # Reporte por severidad
    if high_severity:
        report_lines.append("=" * 80)
        report_lines.append("🔴 ALTA SEVERIDAD - Requiere corrección inmediata")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        for issue in high_severity:
            report_lines.append(f"Archivo: {issue['file']}")
            report_lines.append(f"Línea: {issue['line']}")
            report_lines.append(f"Tabla: {issue.get('tabla', 'N/A')}")
            report_lines.append(f"Tipo: {issue.get('type', 'N/A')}")
            report_lines.append(f"Issue: {issue['issue']}")
            report_lines.append(f"Contexto:")
            report_lines.append(issue.get('context', 'N/A')[:300])
            report_lines.append("-" * 80)
            report_lines.append("")
    
    # Reporte por archivo
    report_lines.append("=" * 80)
    report_lines.append("Reporte por Archivo")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    for file_path, file_issues in sorted(by_file.items()):
        report_lines.append(f"\n{file_path}: {len(file_issues)} issues")
        for issue in file_issues:
            severity_icon = "🔴" if issue.get('severity') == 'high' else "🟡"
            report_lines.append(f"  {severity_icon} Línea {issue['line']}: {issue['issue']}")
    
    report = "\n".join(report_lines)
    
    # Guardar en archivo si se especifica
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # También guardar JSON para procesamiento posterior
        json_file = output_file.with_suffix('.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(issues, f, indent=2, ensure_ascii=False)
        
        print(f"Reporte guardado en: {output_file}")
        print(f"Datos JSON guardados en: {json_file}")
    
    return report


def main():
    """Función principal del script."""
    import sys
    
    # Directorio a auditar (por defecto: app/)
    if len(sys.argv) > 1:
        directory = Path(sys.argv[1])
    else:
        directory = Path('app')
    
    if not directory.exists():
        print(f"Error: Directorio {directory} no existe")
        sys.exit(1)
    
    print(f"Auditando directorio: {directory}")
    print("Buscando queries con text() o string SQL...")
    print("")
    
    # Ejecutar auditoría
    issues = audit_directory(directory)
    
    # Generar reporte
    output_file = Path('reports/audit_text_queries_report.txt')
    report = generate_report(issues, output_file)
    
    # Mostrar resumen (sin emojis para evitar problemas de encoding en Windows)
    try:
        print(report)
    except UnicodeEncodeError:
        # Si hay problema de encoding, mostrar sin emojis
        report_ascii = report.replace('🔴', '[HIGH]').replace('🟡', '[MEDIUM]').replace('✅', '[OK]').replace('⚠️', '[WARN]')
        print(report_ascii)
    
    # Retornar código de salida según severidad
    high_count = len([i for i in issues if i.get('severity') == 'high'])
    if high_count > 0:
        print(f"\n⚠️  Se encontraron {high_count} issues de alta severidad que requieren corrección.")
        sys.exit(1)
    else:
        print("\n✅ No se encontraron issues críticos.")
        sys.exit(0)


if __name__ == '__main__':
    main()
