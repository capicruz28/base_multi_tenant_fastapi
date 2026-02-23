# app/modules/sls/presentation/endpoints.py
"""
Router principal del módulo SLS (Ventas).
Agrupa todos los endpoints de las entidades del módulo.
"""
from fastapi import APIRouter

from app.modules.sls.presentation.endpoints_clientes import router as clientes_router
from app.modules.sls.presentation.endpoints_contactos import router as contactos_router
from app.modules.sls.presentation.endpoints_direcciones import router as direcciones_router
from app.modules.sls.presentation.endpoints_cotizaciones import router as cotizaciones_router
from app.modules.sls.presentation.endpoints_pedidos import router as pedidos_router

router = APIRouter()

# Incluir todos los routers de entidades
router.include_router(clientes_router, prefix="/clientes", tags=["SLS - Clientes"])
router.include_router(contactos_router, prefix="/contactos", tags=["SLS - Contactos"])
router.include_router(direcciones_router, prefix="/direcciones", tags=["SLS - Direcciones"])
router.include_router(cotizaciones_router, prefix="/cotizaciones", tags=["SLS - Cotizaciones"])
router.include_router(pedidos_router, prefix="/pedidos", tags=["SLS - Pedidos"])
