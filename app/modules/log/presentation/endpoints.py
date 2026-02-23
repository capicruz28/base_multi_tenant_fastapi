# app/modules/log/presentation/endpoints.py
"""
Router principal del módulo LOG (Logística y Distribución).
Agrupa todos los endpoints de las entidades del módulo.
"""
from fastapi import APIRouter

from app.modules.log.presentation.endpoints_transportistas import router as transportistas_router
from app.modules.log.presentation.endpoints_vehiculos import router as vehiculos_router
from app.modules.log.presentation.endpoints_rutas import router as rutas_router
from app.modules.log.presentation.endpoints_guias_remision import router as guias_remision_router
from app.modules.log.presentation.endpoints_despachos import router as despachos_router

router = APIRouter()

# Incluir todos los routers de entidades
router.include_router(transportistas_router, prefix="/transportistas", tags=["LOG - Transportistas"])
router.include_router(vehiculos_router, prefix="/vehiculos", tags=["LOG - Vehículos"])
router.include_router(rutas_router, prefix="/rutas", tags=["LOG - Rutas"])
router.include_router(guias_remision_router, prefix="/guias-remision", tags=["LOG - Guías de Remisión"])
router.include_router(despachos_router, prefix="/despachos", tags=["LOG - Despachos"])
