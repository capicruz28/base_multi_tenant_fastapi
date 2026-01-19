# app/core/metrics/basic_metrics.py
"""
Módulo básico de métricas para monitoreo.

✅ FASE 2: PERFORMANCE - Métricas básicas
"""

import time
import logging
from typing import Dict, Any, Optional
from functools import wraps
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

# Almacenamiento simple de métricas (en producción usar Prometheus/StatsD)
_metrics: Dict[str, Any] = {
    'query_times': [],
    'query_counts': defaultdict(int),
    'error_counts': defaultdict(int),
    'tenant_queries': defaultdict(int),
}


def record_query_time(query_name: str, duration: float, client_id: Optional[str] = None):
    """
    Registra el tiempo de ejecución de una query.
    
    Args:
        query_name: Nombre identificador de la query
        duration: Tiempo de ejecución en segundos
        client_id: ID del tenant (opcional)
    """
    _metrics['query_times'].append({
        'query': query_name,
        'duration': duration,
        'client_id': str(client_id) if client_id else None,
        'timestamp': datetime.now().isoformat()
    })
    
    # Mantener solo los últimos 1000 registros
    if len(_metrics['query_times']) > 1000:
        _metrics['query_times'] = _metrics['query_times'][-1000:]
    
    # Contar queries por tenant
    if client_id:
        _metrics['tenant_queries'][str(client_id)] += 1
    
    # Log si es lenta (>100ms)
    if duration > 0.1:
        logger.warning(
            f"[METRICS] Query lenta detectada: {query_name} "
            f"tardó {duration*1000:.2f}ms (tenant: {client_id})"
        )


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
    
    Args:
        error_type: Tipo de error
        details: Detalles adicionales (opcional)
    """
    _metrics['error_counts'][error_type] += 1
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
    }


