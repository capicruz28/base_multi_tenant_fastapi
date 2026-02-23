# app/modules/mrp/presentation/endpoints.py
"""Router principal del módulo MRP (Planeamiento de Materiales)."""
from fastapi import APIRouter
from app.modules.mrp.presentation.endpoints_plan_maestro import router as plan_maestro_router
from app.modules.mrp.presentation.endpoints_necesidad_bruta import router as necesidad_bruta_router
from app.modules.mrp.presentation.endpoints_explosion_materiales import router as explosion_materiales_router
from app.modules.mrp.presentation.endpoints_orden_sugerida import router as orden_sugerida_router

router = APIRouter()

router.include_router(plan_maestro_router, prefix="/plan-maestro", tags=["MRP - Plan Maestro"])
router.include_router(necesidad_bruta_router, prefix="/necesidades-brutas", tags=["MRP - Necesidades Brutas"])
router.include_router(explosion_materiales_router, prefix="/explosion-materiales", tags=["MRP - Explosión Materiales"])
router.include_router(orden_sugerida_router, prefix="/ordenes-sugeridas", tags=["MRP - Órdenes Sugeridas"])
