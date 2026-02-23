# app/infrastructure/database/queries/fin/__init__.py
"""
Queries para el módulo FIN (Finanzas y Contabilidad).
"""

from app.infrastructure.database.queries.fin.plan_cuentas_queries import (
    list_plan_cuentas,
    get_cuenta_by_id,
    create_cuenta,
    update_cuenta,
)
from app.infrastructure.database.queries.fin.periodo_contable_queries import (
    list_periodos_contables,
    get_periodo_contable_by_id,
    create_periodo_contable,
    update_periodo_contable,
)
from app.infrastructure.database.queries.fin.asiento_contable_queries import (
    list_asientos_contables,
    get_asiento_contable_by_id,
    create_asiento_contable,
    update_asiento_contable,
    list_asiento_detalles,
    get_asiento_detalle_by_id,
    create_asiento_detalle,
    update_asiento_detalle,
)

__all__ = [
    # Plan de Cuentas
    "list_plan_cuentas",
    "get_cuenta_by_id",
    "create_cuenta",
    "update_cuenta",
    # Periodos Contables
    "list_periodos_contables",
    "get_periodo_contable_by_id",
    "create_periodo_contable",
    "update_periodo_contable",
    # Asientos Contables
    "list_asientos_contables",
    "get_asiento_contable_by_id",
    "create_asiento_contable",
    "update_asiento_contable",
    # Detalles de Asiento
    "list_asiento_detalles",
    "get_asiento_detalle_by_id",
    "create_asiento_detalle",
    "update_asiento_detalle",
]
