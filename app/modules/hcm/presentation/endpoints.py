# app/modules/hcm/presentation/endpoints.py
"""Router principal del módulo HCM (Planillas y RRHH)."""
from fastapi import APIRouter
from app.modules.hcm.presentation.endpoints_empleados import router as empleados_router
from app.modules.hcm.presentation.endpoints_contratos import router as contratos_router
from app.modules.hcm.presentation.endpoints_conceptos_planilla import router as conceptos_planilla_router
from app.modules.hcm.presentation.endpoints_planillas import router as planillas_router
from app.modules.hcm.presentation.endpoints_planilla_empleados import router as planilla_empleados_router
from app.modules.hcm.presentation.endpoints_planilla_detalle import router as planilla_detalle_router
from app.modules.hcm.presentation.endpoints_asistencia import router as asistencia_router
from app.modules.hcm.presentation.endpoints_vacaciones import router as vacaciones_router
from app.modules.hcm.presentation.endpoints_prestamos import router as prestamos_router

router = APIRouter()

router.include_router(empleados_router, prefix="/empleados", tags=["HCM - Empleados"])
router.include_router(contratos_router, prefix="/contratos", tags=["HCM - Contratos"])
router.include_router(conceptos_planilla_router, prefix="/conceptos-planilla", tags=["HCM - Conceptos Planilla"])
router.include_router(planillas_router, prefix="/planillas", tags=["HCM - Planillas"])
router.include_router(planilla_empleados_router, prefix="/planilla-empleados", tags=["HCM - Planilla Empleados"])
router.include_router(planilla_detalle_router, prefix="/planilla-detalle", tags=["HCM - Planilla Detalle"])
router.include_router(asistencia_router, prefix="/asistencia", tags=["HCM - Asistencia"])
router.include_router(vacaciones_router, prefix="/vacaciones", tags=["HCM - Vacaciones"])
router.include_router(prestamos_router, prefix="/prestamos", tags=["HCM - Préstamos"])
