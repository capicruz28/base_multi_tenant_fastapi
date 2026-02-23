# app/modules/wfl/presentation/endpoints.py
"""Router principal del modulo WFL (Flujos de Trabajo)."""
from fastapi import APIRouter
from app.modules.wfl.presentation.endpoints_flujo_trabajo import router as flujo_trabajo_router

router = APIRouter()

router.include_router(
    flujo_trabajo_router,
    prefix="/flujos-trabajo",
    tags=["WFL - Flujos de Trabajo"],
)
