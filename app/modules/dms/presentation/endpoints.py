# app/modules/dms/presentation/endpoints.py
"""Router principal del modulo DMS (Gestion Documental)."""
from fastapi import APIRouter
from app.modules.dms.presentation.endpoints_documento import router as documento_router

router = APIRouter()

router.include_router(documento_router, prefix="/documentos", tags=["DMS - Documentos"])
