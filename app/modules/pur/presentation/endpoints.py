# app/modules/pur/presentation/endpoints.py
"""
Router principal del módulo PUR (Compras).
Agrupa todos los endpoints de las entidades PUR.
"""
from fastapi import APIRouter

from app.modules.pur.presentation.endpoints_proveedores import router as proveedores_router
from app.modules.pur.presentation.endpoints_contactos import router as contactos_router
from app.modules.pur.presentation.endpoints_productos_proveedor import router as productos_proveedor_router
from app.modules.pur.presentation.endpoints_solicitudes import router as solicitudes_router
from app.modules.pur.presentation.endpoints_cotizaciones import router as cotizaciones_router
from app.modules.pur.presentation.endpoints_ordenes_compra import router as ordenes_compra_router
from app.modules.pur.presentation.endpoints_recepciones import router as recepciones_router

router = APIRouter()

# Incluir todos los routers de entidades PUR
router.include_router(
    proveedores_router,
    prefix="/proveedores",
    tags=["PUR - Proveedores"]
)

router.include_router(
    contactos_router,
    prefix="/contactos",
    tags=["PUR - Contactos de Proveedor"]
)

router.include_router(
    productos_proveedor_router,
    prefix="/productos-proveedor",
    tags=["PUR - Productos por Proveedor"]
)

router.include_router(
    solicitudes_router,
    prefix="/solicitudes",
    tags=["PUR - Solicitudes de Compra"]
)

router.include_router(
    cotizaciones_router,
    prefix="/cotizaciones",
    tags=["PUR - Cotizaciones"]
)

router.include_router(
    ordenes_compra_router,
    prefix="/ordenes-compra",
    tags=["PUR - Órdenes de Compra"]
)

router.include_router(
    recepciones_router,
    prefix="/recepciones",
    tags=["PUR - Recepciones"]
)
