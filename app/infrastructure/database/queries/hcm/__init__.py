# app/infrastructure/database/queries/hcm/__init__.py
"""
Queries para el módulo HCM (Human Capital Management - Planillas y RRHH).
"""
from app.infrastructure.database.queries.hcm.empleado_queries import (
    list_empleados,
    get_empleado_by_id,
    create_empleado,
    update_empleado,
)
from app.infrastructure.database.queries.hcm.contrato_queries import (
    list_contratos,
    get_contrato_by_id,
    create_contrato,
    update_contrato,
)
from app.infrastructure.database.queries.hcm.concepto_planilla_queries import (
    list_conceptos_planilla,
    get_concepto_planilla_by_id,
    create_concepto_planilla,
    update_concepto_planilla,
)
from app.infrastructure.database.queries.hcm.planilla_queries import (
    list_planillas,
    get_planilla_by_id,
    create_planilla,
    update_planilla,
)
from app.infrastructure.database.queries.hcm.planilla_empleado_queries import (
    list_planilla_empleados,
    get_planilla_empleado_by_id,
    create_planilla_empleado,
    update_planilla_empleado,
)
from app.infrastructure.database.queries.hcm.planilla_detalle_queries import (
    list_planilla_detalles,
    get_planilla_detalle_by_id,
    create_planilla_detalle,
    update_planilla_detalle,
)
from app.infrastructure.database.queries.hcm.asistencia_queries import (
    list_asistencias,
    get_asistencia_by_id,
    create_asistencia,
    update_asistencia,
)
from app.infrastructure.database.queries.hcm.vacaciones_queries import (
    list_vacaciones,
    get_vacaciones_by_id,
    create_vacaciones,
    update_vacaciones,
)
from app.infrastructure.database.queries.hcm.prestamo_queries import (
    list_prestamos,
    get_prestamo_by_id,
    create_prestamo,
    update_prestamo,
)

__all__ = [
    "list_empleados",
    "get_empleado_by_id",
    "create_empleado",
    "update_empleado",
    "list_contratos",
    "get_contrato_by_id",
    "create_contrato",
    "update_contrato",
    "list_conceptos_planilla",
    "get_concepto_planilla_by_id",
    "create_concepto_planilla",
    "update_concepto_planilla",
    "list_planillas",
    "get_planilla_by_id",
    "create_planilla",
    "update_planilla",
    "list_planilla_empleados",
    "get_planilla_empleado_by_id",
    "create_planilla_empleado",
    "update_planilla_empleado",
    "list_planilla_detalles",
    "get_planilla_detalle_by_id",
    "create_planilla_detalle",
    "update_planilla_detalle",
    "list_asistencias",
    "get_asistencia_by_id",
    "create_asistencia",
    "update_asistencia",
    "list_vacaciones",
    "get_vacaciones_by_id",
    "create_vacaciones",
    "update_vacaciones",
    "list_prestamos",
    "get_prestamo_by_id",
    "create_prestamo",
    "update_prestamo",
]
