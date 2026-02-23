# app/modules/inv/presentation/endpoints.py
"""
Router principal del módulo INV (Inventarios).
Agrupa todos los endpoints de las entidades INV.
"""
from fastapi import APIRouter

from app.modules.inv.presentation.endpoints_categorias import router as categorias_router
from app.modules.inv.presentation.endpoints_unidades_medida import router as unidades_medida_router
from app.modules.inv.presentation.endpoints_productos import router as productos_router
from app.modules.inv.presentation.endpoints_almacenes import router as almacenes_router
from app.modules.inv.presentation.endpoints_stock import router as stock_router
from app.modules.inv.presentation.endpoints_tipos_movimiento import router as tipos_movimiento_router
from app.modules.inv.presentation.endpoints_movimientos import router as movimientos_router
from app.modules.inv.presentation.endpoints_inventario_fisico import router as inventario_fisico_router

router = APIRouter()

# Incluir todos los routers de entidades INV
router.include_router(
    categorias_router,
    prefix="/categorias",
    tags=["INV - Categorías"]
)

router.include_router(
    unidades_medida_router,
    prefix="/unidades-medida",
    tags=["INV - Unidades de Medida"]
)

router.include_router(
    productos_router,
    prefix="/productos",
    tags=["INV - Productos"]
)

router.include_router(
    almacenes_router,
    prefix="/almacenes",
    tags=["INV - Almacenes"]
)

router.include_router(
    stock_router,
    prefix="/stock",
    tags=["INV - Stock"]
)

router.include_router(
    tipos_movimiento_router,
    prefix="/tipos-movimiento",
    tags=["INV - Tipos de Movimiento"]
)

router.include_router(
    movimientos_router,
    prefix="/movimientos",
    tags=["INV - Movimientos"]
)

router.include_router(
    inventario_fisico_router,
    prefix="/inventario-fisico",
    tags=["INV - Inventario Físico"]
)
