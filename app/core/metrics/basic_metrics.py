# app/core/metrics/basic_metrics.py
"""
Módulo básico de métricas para monitoreo.

✅ FASE 2: PERFORMANCE - Métricas básicas
✅ FASE 1 SEGURIDAD: Mejoras con persistencia y alertas básicas
"""

import time
import logging
import json
import os
from typing import Dict, Any, Optional, List
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuración de persistencia
METRICS_DIR = Path("metrics_data")
METRICS_FILE = METRICS_DIR / "metrics.json"
METRICS_RETENTION_HOURS = 24  # Retener métricas por 24 horas

# Almacenamiento simple de métricas (en producción usar Prometheus/StatsD)
_metrics: Dict[str, Any] = {
    'query_times': [],
    'query_counts': defaultdict(int),
    'error_counts': defaultdict(int),
    'tenant_queries': defaultdict(int),
    'slow_queries': [],  # ✅ NUEVO: Queries lentas para alertas
    'errors_recent': [],  # ✅ NUEVO: Errores recientes para alertas
    'last_cleanup': None,  # ✅ NUEVO: Última limpieza
}


def record_query_time(query_name: str, duration: float, client_id: Optional[str] = None):
    """
    Registra el tiempo de ejecución de una query.
    
    ✅ FASE 1 SEGURIDAD: Mejorado con alertas y persistencia.
    
    Args:
        query_name: Nombre identificador de la query
        duration: Tiempo de ejecución en segundos
        client_id: ID del tenant (opcional)
    """
    timestamp = datetime.now()
    query_record = {
        'query': query_name,
        'duration': duration,
        'client_id': str(client_id) if client_id else None,
        'timestamp': timestamp.isoformat()
    }
    
    _metrics['query_times'].append(query_record)
    
    # Mantener solo los últimos 1000 registros
    if len(_metrics['query_times']) > 1000:
        _metrics['query_times'] = _metrics['query_times'][-1000:]
    
    # Contar queries por tenant
    if client_id:
        _metrics['tenant_queries'][str(client_id)] += 1
    
    # ✅ NUEVO: Alertas para queries lentas (>100ms = warning, >500ms = error)
    if duration > 0.5:
        logger.error(
            f"[METRICS-ALERT] Query MUY LENTA: {query_name} "
            f"tardó {duration*1000:.2f}ms (tenant: {client_id})"
        )
        _metrics['slow_queries'].append({
            **query_record,
            'severity': 'error',
            'threshold_ms': 500
        })
    elif duration > 0.1:
        logger.warning(
            f"[METRICS-ALERT] Query lenta detectada: {query_name} "
            f"tardó {duration*1000:.2f}ms (tenant: {client_id})"
        )
        _metrics['slow_queries'].append({
            **query_record,
            'severity': 'warning',
            'threshold_ms': 100
        })
    
    # Mantener solo los últimos 100 queries lentas
    if len(_metrics['slow_queries']) > 100:
        _metrics['slow_queries'] = _metrics['slow_queries'][-100:]


def record_query_execution(query_name: str, success: bool = True):
    """
    Registra la ejecución de una query.
    
    Args:
        query_name: Nombre identificador de la query
        success: Si la query fue exitosa
    """
    _metrics['query_counts'][query_name] += 1
    
    if not success:
        _metrics['error_counts'][query_name] += 1


def record_error(error_type: str, details: Optional[str] = None):
    """
    Registra un error.
    
    ✅ FASE 1 SEGURIDAD: Mejorado con registro de errores recientes.
    
    Args:
        error_type: Tipo de error
        details: Detalles adicionales (opcional)
    """
    _metrics['error_counts'][error_type] += 1
    
    error_record = {
        'error_type': error_type,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }
    
    _metrics['errors_recent'].append(error_record)
    
    # Mantener solo los últimos 200 errores
    if len(_metrics['errors_recent']) > 200:
        _metrics['errors_recent'] = _metrics['errors_recent'][-200:]
    
    logger.error(f"[METRICS] Error registrado: {error_type} - {details}")


def query_timer(query_name: str):
    """
    Decorador para medir tiempo de ejecución de queries.
    
    Uso:
        @query_timer("get_user")
        async def get_user(user_id: UUID):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Extraer client_id de args/kwargs si está disponible
                client_id = None
                if 'client_id' in kwargs:
                    client_id = kwargs['client_id']
                elif args and hasattr(args[0], 'client_id'):
                    client_id = getattr(args[0], 'client_id', None)
                
                record_query_time(query_name, duration, client_id)
                record_query_execution(query_name, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                record_query_time(query_name, duration)
                record_query_execution(query_name, success=False)
                record_error(f"{query_name}_error", str(e))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                record_query_time(query_name, duration)
                record_query_execution(query_name, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                record_query_time(query_name, duration)
                record_query_execution(query_name, success=False)
                record_error(f"{query_name}_error", str(e))
                raise
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_metrics_summary() -> Dict[str, Any]:
    """
    Obtiene un resumen de las métricas.
    
    ✅ FASE 1 SEGURIDAD: Mejorado con información de alertas.
    
    Returns:
        Dict con resumen de métricas
    """
    query_times = _metrics['query_times']
    
    if not query_times:
        return {
            'total_queries': 0,
            'queries_by_name': dict(_metrics['query_counts']),
            'errors_by_type': dict(_metrics['error_counts']),
            'queries_by_tenant': dict(_metrics['tenant_queries']),
            'recent_errors': get_recent_errors(5),
            'recent_slow_queries': get_recent_slow_queries(5),
            'last_cleanup': _metrics['last_cleanup'],
        }
    
    durations = [q['duration'] for q in query_times]
    
    return {
        'total_queries': len(query_times),
        'query_times': {
            'min': min(durations) * 1000,  # en ms
            'max': max(durations) * 1000,
            'avg': (sum(durations) / len(durations)) * 1000,
            'p50': sorted(durations)[len(durations) // 2] * 1000,
            'p95': sorted(durations)[int(len(durations) * 0.95)] * 1000,
            'p99': sorted(durations)[int(len(durations) * 0.99)] * 1000,
        },
        'queries_by_name': dict(_metrics['query_counts']),
        'errors_by_type': dict(_metrics['error_counts']),
        'queries_by_tenant': dict(_metrics['tenant_queries']),
        'recent_errors': get_recent_errors(5),
        'recent_slow_queries': get_recent_slow_queries(5),
        'slow_queries_count': len(_metrics['slow_queries']),
        'errors_recent_count': len(_metrics['errors_recent']),
        'last_cleanup': _metrics['last_cleanup'],
    }


def get_slow_queries(threshold_ms: float = 100.0, limit: int = 10) -> list:
    """
    Obtiene las queries más lentas.
    
    Args:
        threshold_ms: Umbral en milisegundos
        limit: Número máximo de resultados
    
    Returns:
        Lista de queries lentas ordenadas por tiempo
    """
    slow_queries = [
        q for q in _metrics['query_times']
        if q['duration'] * 1000 > threshold_ms
    ]
    
    slow_queries.sort(key=lambda x: x['duration'], reverse=True)
    return slow_queries[:limit]


def reset_metrics():
    """Resetea todas las métricas (útil para tests)."""
    global _metrics
    _metrics = {
        'query_times': [],
        'query_counts': defaultdict(int),
        'error_counts': defaultdict(int),
        'tenant_queries': defaultdict(int),
        'slow_queries': [],
        'errors_recent': [],
        'last_cleanup': None,
    }


def cleanup_old_metrics():
    """
    Limpia métricas antiguas (más de METRICS_RETENTION_HOURS horas).
    
    ✅ FASE 1 SEGURIDAD: Nueva función para limpieza automática.
    """
    cutoff_time = datetime.now() - timedelta(hours=METRICS_RETENTION_HOURS)
    
    # Limpiar query_times antiguas
    _metrics['query_times'] = [
        q for q in _metrics['query_times']
        if datetime.fromisoformat(q['timestamp']) > cutoff_time
    ]
    
    # Limpiar slow_queries antiguas
    _metrics['slow_queries'] = [
        q for q in _metrics['slow_queries']
        if datetime.fromisoformat(q['timestamp']) > cutoff_time
    ]
    
    # Limpiar errors_recent antiguos
    _metrics['errors_recent'] = [
        e for e in _metrics['errors_recent']
        if datetime.fromisoformat(e['timestamp']) > cutoff_time
    ]
    
    _metrics['last_cleanup'] = datetime.now().isoformat()
    logger.info(f"[METRICS] Limpieza de métricas antiguas completada - Retención: {METRICS_RETENTION_HOURS}h")


def save_metrics_to_file():
    """
    Guarda las métricas en un archivo JSON para persistencia.
    
    ✅ FASE 1 SEGURIDAD: Nueva función para persistencia.
    """
    try:
        METRICS_DIR.mkdir(exist_ok=True)
        
        # Convertir defaultdict a dict para serialización
        metrics_to_save = {
            'query_times': _metrics['query_times'],
            'query_counts': dict(_metrics['query_counts']),
            'error_counts': dict(_metrics['error_counts']),
            'tenant_queries': dict(_metrics['tenant_queries']),
            'slow_queries': _metrics['slow_queries'],
            'errors_recent': _metrics['errors_recent'],
            'last_cleanup': _metrics['last_cleanup'],
            'last_saved': datetime.now().isoformat()
        }
        
        with open(METRICS_FILE, 'w') as f:
            json.dump(metrics_to_save, f, indent=2, default=str)
        
        logger.debug(f"[METRICS] Métricas guardadas en {METRICS_FILE}")
    except Exception as e:
        logger.warning(f"[METRICS] Error guardando métricas: {e}")


def load_metrics_from_file():
    """
    Carga las métricas desde un archivo JSON.
    
    ✅ FASE 1 SEGURIDAD: Nueva función para carga de métricas persistentes.
    """
    try:
        if METRICS_FILE.exists():
            with open(METRICS_FILE, 'r') as f:
                loaded = json.load(f)
            
            # Restaurar métricas
            _metrics['query_times'] = loaded.get('query_times', [])
            _metrics['query_counts'] = defaultdict(int, loaded.get('query_counts', {}))
            _metrics['error_counts'] = defaultdict(int, loaded.get('error_counts', {}))
            _metrics['tenant_queries'] = defaultdict(int, loaded.get('tenant_queries', {}))
            _metrics['slow_queries'] = loaded.get('slow_queries', [])
            _metrics['errors_recent'] = loaded.get('errors_recent', [])
            _metrics['last_cleanup'] = loaded.get('last_cleanup')
            
            logger.info(f"[METRICS] Métricas cargadas desde {METRICS_FILE}")
    except Exception as e:
        logger.warning(f"[METRICS] Error cargando métricas: {e}")


def get_recent_errors(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Obtiene los errores más recientes.
    
    ✅ FASE 1 SEGURIDAD: Nueva función para alertas.
    
    Args:
        limit: Número máximo de errores a retornar
    
    Returns:
        Lista de errores recientes ordenados por timestamp (más reciente primero)
    """
    errors = sorted(
        _metrics['errors_recent'],
        key=lambda x: x['timestamp'],
        reverse=True
    )
    return errors[:limit]


def get_recent_slow_queries(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Obtiene las queries más lentas recientes.
    
    ✅ FASE 1 SEGURIDAD: Nueva función para alertas.
    
    Args:
        limit: Número máximo de queries a retornar
    
    Returns:
        Lista de queries lentas ordenadas por tiempo (más lentas primero)
    """
    slow = sorted(
        _metrics['slow_queries'],
        key=lambda x: x['duration'],
        reverse=True
    )
    return slow[:limit]


