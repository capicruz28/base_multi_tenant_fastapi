# app/modules/mnt/presentation/endpoints.py
"""Router principal del módulo MNT (Mantenimiento de Activos)."""
from fastapi import APIRouter
from app.modules.mnt.presentation.endpoints_activo import router as activo_router
from app.modules.mnt.presentation.endpoints_plan_mantenimiento import router as plan_mantenimiento_router
from app.modules.mnt.presentation.endpoints_orden_trabajo import router as orden_trabajo_router
from app.modules.mnt.presentation.endpoints_historial_mantenimiento import router as historial_mantenimiento_router

router = APIRouter()

router.include_router(activo_router, prefix="/activos", tags=["MNT - Activos"])
router.include_router(plan_mantenimiento_router, prefix="/planes-mantenimiento", tags=["MNT - Planes Mantenimiento"])
router.include_router(orden_trabajo_router, prefix="/ordenes-trabajo", tags=["MNT - Órdenes de Trabajo"])
router.include_router(historial_mantenimiento_router, prefix="/historial-mantenimiento", tags=["MNT - Historial Mantenimiento"])
