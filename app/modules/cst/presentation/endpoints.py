# app/modules/cst/presentation/endpoints.py
"""Router principal del modulo CST (Costeo de Productos)."""
from fastapi import APIRouter
from app.modules.cst.presentation.endpoints_centro_costo_tipo import router as centro_costo_tipo_router
from app.modules.cst.presentation.endpoints_producto_costo import router as producto_costo_router

router = APIRouter()

router.include_router(centro_costo_tipo_router, prefix="/tipos-centro-costo", tags=["CST - Tipos Centro Costo"])
router.include_router(producto_costo_router, prefix="/producto-costo", tags=["CST - Costo de Productos"])
