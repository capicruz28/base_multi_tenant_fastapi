# app/modules/bi/presentation/endpoints.py
"""Router principal del modulo BI (Reportes & Analytics)."""
from fastapi import APIRouter
from app.modules.bi.presentation.endpoints_reporte import router as reporte_router

router = APIRouter()

router.include_router(
    reporte_router,
    prefix="/reportes",
    tags=["BI - Reportes"],
)
