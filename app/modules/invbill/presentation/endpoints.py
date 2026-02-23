# app/modules/invbill/presentation/endpoints.py
"""
Router principal del módulo INV_BILL (Facturación Electrónica).
Agrupa todos los endpoints de las entidades del módulo.
"""
from fastapi import APIRouter

from app.modules.invbill.presentation.endpoints_series import router as series_router
from app.modules.invbill.presentation.endpoints_comprobantes import router as comprobantes_router
from app.modules.invbill.presentation.endpoints_comprobante_detalles import router as detalles_router

router = APIRouter()

# Incluir todos los routers de entidades
router.include_router(series_router, prefix="/series", tags=["INV_BILL - Series"])
router.include_router(comprobantes_router, prefix="/comprobantes", tags=["INV_BILL - Comprobantes"])
router.include_router(detalles_router, prefix="/comprobantes-detalles", tags=["INV_BILL - Detalles"])
