# app/modules/wms/presentation/endpoints.py
"""
Router principal del módulo WMS (Warehouse Management System).
Agrupa todos los endpoints de las entidades del módulo.
"""
from fastapi import APIRouter

from app.modules.wms.presentation.endpoints_zonas import router as zonas_router
from app.modules.wms.presentation.endpoints_ubicaciones import router as ubicaciones_router
from app.modules.wms.presentation.endpoints_stock import router as stock_router
from app.modules.wms.presentation.endpoints_tareas import router as tareas_router

router = APIRouter()

# Incluir todos los routers de entidades
router.include_router(zonas_router, prefix="/zonas", tags=["WMS - Zonas de Almacén"])
router.include_router(ubicaciones_router, prefix="/ubicaciones", tags=["WMS - Ubicaciones"])
router.include_router(stock_router, prefix="/stock-ubicacion", tags=["WMS - Stock por Ubicación"])
router.include_router(tareas_router, prefix="/tareas", tags=["WMS - Tareas"])
