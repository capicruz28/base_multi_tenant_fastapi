# app/modules/mfg/presentation/endpoints.py
"""Router principal del módulo MFG (Manufactura y Producción)."""
from fastapi import APIRouter
from app.modules.mfg.presentation.endpoints_centros_trabajo import router as centros_trabajo_router
from app.modules.mfg.presentation.endpoints_operaciones import router as operaciones_router
from app.modules.mfg.presentation.endpoints_listas_materiales import router as listas_materiales_router
from app.modules.mfg.presentation.endpoints_lista_materiales_detalle import router as lista_materiales_detalle_router
from app.modules.mfg.presentation.endpoints_rutas_fabricacion import router as rutas_fabricacion_router
from app.modules.mfg.presentation.endpoints_ruta_fabricacion_detalle import router as ruta_fabricacion_detalle_router
from app.modules.mfg.presentation.endpoints_ordenes_produccion import router as ordenes_produccion_router
from app.modules.mfg.presentation.endpoints_orden_produccion_operaciones import router as orden_produccion_operaciones_router
from app.modules.mfg.presentation.endpoints_consumo_materiales import router as consumo_materiales_router

router = APIRouter()

router.include_router(centros_trabajo_router, prefix="/centros-trabajo", tags=["MFG - Centros de Trabajo"])
router.include_router(operaciones_router, prefix="/operaciones", tags=["MFG - Operaciones"])
router.include_router(listas_materiales_router, prefix="/listas-materiales", tags=["MFG - Listas de Materiales (BOM)"])
router.include_router(lista_materiales_detalle_router, prefix="/lista-materiales-detalle", tags=["MFG - BOM Detalle"])
router.include_router(rutas_fabricacion_router, prefix="/rutas-fabricacion", tags=["MFG - Rutas de Fabricación"])
router.include_router(ruta_fabricacion_detalle_router, prefix="/ruta-fabricacion-detalle", tags=["MFG - Ruta Fabricación Detalle"])
router.include_router(ordenes_produccion_router, prefix="/ordenes-produccion", tags=["MFG - Órdenes de Producción"])
router.include_router(orden_produccion_operaciones_router, prefix="/orden-produccion-operaciones", tags=["MFG - OP Operaciones"])
router.include_router(consumo_materiales_router, prefix="/consumo-materiales", tags=["MFG - Consumo Materiales"])
