# app/modules/aud/presentation/endpoints.py
"""Router principal del modulo AUD (Auditoría y Trazabilidad)."""
from fastapi import APIRouter
from app.modules.aud.presentation.endpoints_log_auditoria import router as log_auditoria_router

router = APIRouter()

router.include_router(
    log_auditoria_router,
    prefix="/log-auditoria",
    tags=["AUD - Log de Auditoría"],
)
