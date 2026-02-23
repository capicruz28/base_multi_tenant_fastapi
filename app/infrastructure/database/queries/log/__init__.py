# app/infrastructure/database/queries/log/__init__.py
"""
Queries para el módulo LOG (Logística y Distribución).
"""

from app.infrastructure.database.queries.log.transportista_queries import (
    list_transportistas,
    get_transportista_by_id,
    create_transportista,
    update_transportista,
)
from app.infrastructure.database.queries.log.vehiculo_queries import (
    list_vehiculos,
    get_vehiculo_by_id,
    create_vehiculo,
    update_vehiculo,
)
from app.infrastructure.database.queries.log.ruta_queries import (
    list_rutas,
    get_ruta_by_id,
    create_ruta,
    update_ruta,
)
from app.infrastructure.database.queries.log.guia_remision_queries import (
    list_guias_remision,
    get_guia_remision_by_id,
    create_guia_remision,
    update_guia_remision,
    list_guia_remision_detalles,
    get_guia_remision_detalle_by_id,
    create_guia_remision_detalle,
    update_guia_remision_detalle,
)
from app.infrastructure.database.queries.log.despacho_queries import (
    list_despachos,
    get_despacho_by_id,
    create_despacho,
    update_despacho,
    list_despacho_guias,
    get_despacho_guia_by_id,
    create_despacho_guia,
    update_despacho_guia,
)

__all__ = [
    # Transportistas
    "list_transportistas",
    "get_transportista_by_id",
    "create_transportista",
    "update_transportista",
    # Vehículos
    "list_vehiculos",
    "get_vehiculo_by_id",
    "create_vehiculo",
    "update_vehiculo",
    # Rutas
    "list_rutas",
    "get_ruta_by_id",
    "create_ruta",
    "update_ruta",
    # Guías de Remisión
    "list_guias_remision",
    "get_guia_remision_by_id",
    "create_guia_remision",
    "update_guia_remision",
    # Detalles de Guía
    "list_guia_remision_detalles",
    "get_guia_remision_detalle_by_id",
    "create_guia_remision_detalle",
    "update_guia_remision_detalle",
    # Despachos
    "list_despachos",
    "get_despacho_by_id",
    "create_despacho",
    "update_despacho",
    # Despacho-Guía
    "list_despacho_guias",
    "get_despacho_guia_by_id",
    "create_despacho_guia",
    "update_despacho_guia",
]
