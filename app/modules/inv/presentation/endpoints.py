# app/modules/inv/presentation/endpoints.py
"""
Router principal del módulo INV (Inventarios).
Agrupa todos los endpoints de las entidades INV.
"""
from fastapi import APIRouter, Depends

from app.api.deps_auth import require_erp_session
from app.modules.inv.presentation.endpoints_categorias import router as categorias_router
from app.modules.inv.presentation.endpoints_unidades_medida import router as unidades_medida_router
from app.modules.inv.presentation.endpoints_productos import router as productos_router
from app.modules.inv.presentation.endpoints_almacenes import router as almacenes_router
from app.modules.inv.presentation.endpoints_stock import router as stock_router
from app.modules.inv.presentation.endpoints_stock_alertas import router as stock_alertas_router
from app.modules.inv.presentation.endpoints_tipos_movimiento import router as tipos_movimiento_router
from app.modules.inv.presentation.endpoints_movimientos import router as movimientos_router
from app.modules.inv.presentation.endpoints_movimientos_detalle import router as movimientos_detalle_router
from app.modules.inv.presentation.endpoints_movimientos_proceso import router as movimientos_proceso_router
from app.modules.inv.presentation.endpoints_inventario_fisico import router as inventario_fisico_router
from app.modules.inv.presentation.endpoints_inventario_fisico_aprobar import router as inventario_fisico_aprobar_router
from app.modules.inv.presentation.endpoints_inventario_fisico_detalle import router as inventario_fisico_detalle_router
from app.modules.inv.presentation.endpoints_kardex import router as kardex_router

router = APIRouter(dependencies=[Depends(require_erp_session)])

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
    stock_alertas_router,
    prefix="/stock/alertas",
    tags=["INV - Stock Alertas"]
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

router.include_router(
    inventario_fisico_aprobar_router,
    prefix="/inventario-fisico",
    tags=["INV - Inventario Físico Proceso"]
)

router.include_router(
    movimientos_detalle_router,
    prefix="/movimientos-detalle",
    tags=["INV - Movimientos Detalle"]
)

router.include_router(
    inventario_fisico_detalle_router,
    prefix="/inventario-fisico-detalle",
    tags=["INV - Inventario Físico Detalle"]
)

router.include_router(
    movimientos_proceso_router,
    tags=["INV - Movimientos Proceso"]
)

router.include_router(
    kardex_router,
    prefix="/kardex",
    tags=["INV - Kardex"]
)
