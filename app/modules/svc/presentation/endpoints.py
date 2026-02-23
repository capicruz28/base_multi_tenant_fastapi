# app/modules/svc/presentation/endpoints.py
"""Router principal del modulo SVC (Ordenes de Servicio)."""
from fastapi import APIRouter
from app.modules.svc.presentation.endpoints_orden_servicio import router as orden_servicio_router

router = APIRouter()

router.include_router(
    orden_servicio_router,
    prefix="/ordenes-servicio",
    tags=["SVC - Ordenes de Servicio"],
)
