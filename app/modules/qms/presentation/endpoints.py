# app/modules/qms/presentation/endpoints.py
"""
Router principal del módulo QMS (Quality Management System).
Agrupa todos los endpoints de las entidades del módulo.
"""
from fastapi import APIRouter

from app.modules.qms.presentation.endpoints_parametros import router as parametros_router
from app.modules.qms.presentation.endpoints_planes import router as planes_router
from app.modules.qms.presentation.endpoints_inspecciones import router as inspecciones_router
from app.modules.qms.presentation.endpoints_no_conformidades import router as no_conformidades_router

router = APIRouter()

# Incluir todos los routers de entidades
router.include_router(parametros_router, prefix="/parametros-calidad", tags=["QMS - Parámetros de Calidad"])
router.include_router(planes_router, prefix="/planes-inspeccion", tags=["QMS - Planes de Inspección"])
router.include_router(inspecciones_router, prefix="/inspecciones", tags=["QMS - Inspecciones"])
router.include_router(no_conformidades_router, prefix="/no-conformidades", tags=["QMS - No Conformidades"])
