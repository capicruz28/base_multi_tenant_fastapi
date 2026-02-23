# app/infrastructure/database/queries/org/__init__.py
"""
Queries para el módulo ORG (Organización).

Todas las queries reciben client_id y aplican filtro de tenant estricto.
"""

from app.infrastructure.database.queries.org.empresa_queries import (
    list_empresas,
    get_empresa_by_id,
    create_empresa,
    update_empresa,
)
from app.infrastructure.database.queries.org.centro_costo_queries import (
    list_centros_costo,
    get_centro_costo_by_id,
    create_centro_costo,
    update_centro_costo,
)
from app.infrastructure.database.queries.org.sucursal_queries import (
    list_sucursales,
    get_sucursal_by_id,
    create_sucursal,
    update_sucursal,
)
from app.infrastructure.database.queries.org.departamento_queries import (
    list_departamentos,
    get_departamento_by_id,
    create_departamento,
    update_departamento,
)
from app.infrastructure.database.queries.org.cargo_queries import (
    list_cargos,
    get_cargo_by_id,
    create_cargo,
    update_cargo,
)
from app.infrastructure.database.queries.org.parametro_queries import (
    list_parametros,
    get_parametro_by_id,
    create_parametro,
    update_parametro,
)

__all__ = [
    "list_empresas",
    "get_empresa_by_id",
    "create_empresa",
    "update_empresa",
    "list_centros_costo",
    "get_centro_costo_by_id",
    "create_centro_costo",
    "update_centro_costo",
    "list_sucursales",
    "get_sucursal_by_id",
    "create_sucursal",
    "update_sucursal",
    "list_departamentos",
    "get_departamento_by_id",
    "create_departamento",
    "update_departamento",
    "list_cargos",
    "get_cargo_by_id",
    "create_cargo",
    "update_cargo",
    "list_parametros",
    "get_parametro_by_id",
    "create_parametro",
    "update_parametro",
]
