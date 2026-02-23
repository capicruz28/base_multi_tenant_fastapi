# app/modules/mps/presentation/endpoints.py
"""Router principal del módulo MPS (Plan Maestro de Producción)."""
from fastapi import APIRouter
from app.modules.mps.presentation.endpoints_pronostico_demanda import router as pronostico_demanda_router
from app.modules.mps.presentation.endpoints_plan_produccion import router as plan_produccion_router
from app.modules.mps.presentation.endpoints_plan_produccion_detalle import router as plan_produccion_detalle_router

router = APIRouter()

router.include_router(pronostico_demanda_router, prefix="/pronostico-demanda", tags=["MPS - Pronóstico Demanda"])
router.include_router(plan_produccion_router, prefix="/plan-produccion", tags=["MPS - Plan de Producción"])
router.include_router(plan_produccion_detalle_router, prefix="/plan-produccion-detalle", tags=["MPS - Plan Producción Detalle"])
