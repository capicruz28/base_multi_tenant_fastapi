# app/modules/qms/application/services/__init__.py
"""
Servicios de aplicación para el módulo QMS (Quality Management System).
"""

from app.modules.qms.application.services.parametro_calidad_service import (
    list_parametros_calidad,
    get_parametro_calidad_by_id,
    create_parametro_calidad,
    update_parametro_calidad,
)
from app.modules.qms.application.services.plan_inspeccion_service import (
    list_planes_inspeccion,
    get_plan_inspeccion_by_id,
    create_plan_inspeccion,
    update_plan_inspeccion,
    list_plan_inspeccion_detalles,
    get_plan_inspeccion_detalle_by_id,
    create_plan_inspeccion_detalle,
    update_plan_inspeccion_detalle,
)
from app.modules.qms.application.services.inspeccion_service import (
    list_inspecciones,
    get_inspeccion_by_id,
    create_inspeccion,
    update_inspeccion,
    list_inspeccion_detalles,
    get_inspeccion_detalle_by_id,
    create_inspeccion_detalle,
    update_inspeccion_detalle,
)
from app.modules.qms.application.services.no_conformidad_service import (
    list_no_conformidades,
    get_no_conformidad_by_id,
    create_no_conformidad,
    update_no_conformidad,
)

__all__ = [
    # Parámetros de Calidad
    "list_parametros_calidad",
    "get_parametro_calidad_by_id",
    "create_parametro_calidad",
    "update_parametro_calidad",
    # Planes de Inspección
    "list_planes_inspeccion",
    "get_plan_inspeccion_by_id",
    "create_plan_inspeccion",
    "update_plan_inspeccion",
    "list_plan_inspeccion_detalles",
    "get_plan_inspeccion_detalle_by_id",
    "create_plan_inspeccion_detalle",
    "update_plan_inspeccion_detalle",
    # Inspecciones
    "list_inspecciones",
    "get_inspeccion_by_id",
    "create_inspeccion",
    "update_inspeccion",
    "list_inspeccion_detalles",
    "get_inspeccion_detalle_by_id",
    "create_inspeccion_detalle",
    "update_inspeccion_detalle",
    # No Conformidades
    "list_no_conformidades",
    "get_no_conformidad_by_id",
    "create_no_conformidad",
    "update_no_conformidad",
]
