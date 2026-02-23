# app/modules/pos/presentation/endpoints.py
"""
Router principal del módulo POS (Punto de Venta).
Agrupa todos los endpoints de las entidades del módulo.
"""
from fastapi import APIRouter

from app.modules.pos.presentation.endpoints_puntos_venta import router as puntos_venta_router
from app.modules.pos.presentation.endpoints_turnos_caja import router as turnos_caja_router
from app.modules.pos.presentation.endpoints_ventas import router as ventas_router
from app.modules.pos.presentation.endpoints_ventas_detalle import router as ventas_detalle_router

router = APIRouter()

router.include_router(puntos_venta_router, prefix="/puntos-venta", tags=["POS - Puntos de Venta"])
router.include_router(turnos_caja_router, prefix="/turnos-caja", tags=["POS - Turnos de Caja"])
router.include_router(ventas_router, prefix="/ventas", tags=["POS - Ventas"])
router.include_router(ventas_detalle_router, prefix="/ventas-detalle", tags=["POS - Detalle de Ventas"])
