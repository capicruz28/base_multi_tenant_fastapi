# app/modules/bdg/presentation/endpoints.py
"""Router principal del modulo BDG (Presupuestos)."""
from fastapi import APIRouter
from app.modules.bdg.presentation.endpoints_presupuesto import router as presupuesto_router
from app.modules.bdg.presentation.endpoints_presupuesto_detalle import router as presupuesto_detalle_router

router = APIRouter()

router.include_router(presupuesto_router, prefix="/presupuestos", tags=["BDG - Presupuestos"])
router.include_router(
    presupuesto_detalle_router,
    prefix="/presupuesto-detalle",
    tags=["BDG - Presupuesto Detalle"],
)
