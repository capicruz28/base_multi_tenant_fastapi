# app/modules/prc/presentation/endpoints.py
"""
Router principal del módulo PRC (Gestión de Precios y Promociones).
Agrupa todos los endpoints de las entidades del módulo.
"""
from fastapi import APIRouter

from app.modules.prc.presentation.endpoints_listas_precio import router as listas_precio_router
from app.modules.prc.presentation.endpoints_promociones import router as promociones_router

router = APIRouter()

# Incluir todos los routers de entidades
router.include_router(listas_precio_router, prefix="/listas-precio", tags=["PRC - Listas de Precio"])
router.include_router(promociones_router, prefix="/promociones", tags=["PRC - Promociones"])
