# app/modules/fin/presentation/endpoints.py
"""
Router principal del módulo FIN (Finanzas y Contabilidad).
Agrupa todos los endpoints de las entidades del módulo.
"""
from fastapi import APIRouter

from app.modules.fin.presentation.endpoints_plan_cuentas import router as plan_cuentas_router
from app.modules.fin.presentation.endpoints_periodos import router as periodos_router
from app.modules.fin.presentation.endpoints_asientos import router as asientos_router

router = APIRouter()

# Incluir todos los routers de entidades
router.include_router(plan_cuentas_router, prefix="/plan-cuentas", tags=["FIN - Plan de Cuentas"])
router.include_router(periodos_router, prefix="/periodos", tags=["FIN - Periodos Contables"])
router.include_router(asientos_router, prefix="/asientos", tags=["FIN - Asientos Contables"])
