# app/api/metrics_endpoint.py
"""
Endpoint para exponer métricas básicas.

✅ FASE 2: PERFORMANCE - Endpoint de métricas
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.core.metrics.basic_metrics import get_metrics_summary, get_slow_queries
from app.core.authorization.rbac import require_super_admin

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.get("/summary", response_model=Dict[str, Any])
async def get_metrics(
    current_user: dict = Depends(require_super_admin)
):
    """
    Obtiene resumen de métricas del sistema.
    
    Requiere permisos de SuperAdmin.
    """
    summary = get_metrics_summary()
    return summary


@router.get("/slow-queries", response_model=list)
async def get_slow_queries_endpoint(
    threshold_ms: float = 100.0,
    limit: int = 10,
    current_user: dict = Depends(require_super_admin)
):
    """
    Obtiene las queries más lentas.
    
    Args:
        threshold_ms: Umbral en milisegundos (default: 100ms)
        limit: Número máximo de resultados (default: 10)
    
    Requiere permisos de SuperAdmin.
    """
    slow_queries = get_slow_queries(threshold_ms=threshold_ms, limit=limit)
    return slow_queries


