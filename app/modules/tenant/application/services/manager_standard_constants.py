"""
T2 — MANAGER_STANDARD: bundle estándar para MANAGER_TENANT.

Incluye:
- rol_permiso (API RBAC)
- rol_menu_permiso (visibilidad UI de /auth/menu)

Restricciones funcionales aprobadas:
- MANAGER_TENANT NO administra empresas (solo org.empresa.leer)
- MANAGER_TENANT NO puede eliminar (no incluye *.eliminar; UI puede_eliminar=0)
"""

from __future__ import annotations

from uuid import UUID

MANAGER_ROL_CODIGO = "MANAGER_TENANT"

# Menús ORG/INV visibles para manager estándar (sin Kardex).
# Fuente: catálogo central modulo_menu (ver docs/auditoria/MANAGER_STANDARD_BUNDLE_DESIGN.md)
MANAGER_STANDARD_MENU_GRANTS: tuple[tuple[UUID, dict], ...] = (
    # ORG (catálogos)
    (UUID("E3010001-0000-4000-8000-000000000001"), {"ver": 1, "crear": 1, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # ORG_MI_EMPRESA
    (UUID("E3010002-0000-4000-8000-000000000002"), {"ver": 1, "crear": 1, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # ORG_SUCURSALES
    (UUID("E3010003-0000-4000-8000-000000000003"), {"ver": 1, "crear": 1, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # ORG_DEPARTAMENTOS
    (UUID("E3010004-0000-4000-8000-000000000004"), {"ver": 1, "crear": 1, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # ORG_CARGOS
    (UUID("E3010005-0000-4000-8000-000000000005"), {"ver": 1, "crear": 1, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # ORG_CENTROS_COSTO
    (UUID("E3010006-0000-4000-8000-000000000006"), {"ver": 1, "crear": 1, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # ORG_PARAMETROS

    # INV (catálogos)
    (UUID("E3020002-0000-4000-8000-000000000001"), {"ver": 1, "crear": 1, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_CATEGORIAS
    (UUID("E3020001-0000-4000-8000-000000000002"), {"ver": 1, "crear": 1, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_PRODUCTOS
    (UUID("E3020003-0000-4000-8000-000000000003"), {"ver": 1, "crear": 1, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_UNIDADES
    (UUID("E3020004-0000-4000-8000-000000000004"), {"ver": 1, "crear": 1, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_ALMACENES
    (UUID("E3020006-0000-4000-8000-000000000006"), {"ver": 1, "crear": 1, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_TIPOS_MOV

    # INV (operativo)
    (UUID("E3020005-0000-4000-8000-000000000005"), {"ver": 1, "crear": 0, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_STOCK
    (UUID("E3020007-0000-4000-8000-000000000007"), {"ver": 1, "crear": 1, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 1, "aprobar": 1}),  # INV_MOVIMIENTOS
    (UUID("E3020008-0000-4000-8000-000000000008"), {"ver": 1, "crear": 1, "editar": 1, "eliminar": 0, "exportar": 1, "imprimir": 1, "aprobar": 1}),  # INV_INV_FISICO
)

# Permisos API para MANAGER_STANDARD (47 códigos).
# Incluye BASE_OPERATIVE y permisos ORG/INV (sin eliminar; empresa solo leer).
MANAGER_STANDARD_PERMISSION_CODIGOS: tuple[str, ...] = (
    # BASE_OPERATIVE (T1)
    "core.app.acceder",
    "tenant.branding.leer",
    "org.empresa.leer",

    # ORG (sin eliminar; empresa solo leer)
    "org.sucursal.leer",
    "org.sucursal.crear",
    "org.sucursal.actualizar",
    "org.departamento.leer",
    "org.departamento.crear",
    "org.departamento.actualizar",
    "org.cargo.leer",
    "org.cargo.crear",
    "org.cargo.actualizar",
    "org.centro_costo.leer",
    "org.centro_costo.crear",
    "org.centro_costo.actualizar",
    "org.parametro.leer",
    "org.parametro.crear",
    "org.parametro.actualizar",

    # INV catálogos (sin eliminar)
    "inv.categoria.leer",
    "inv.categoria.crear",
    "inv.categoria.actualizar",
    "inv.producto.leer",
    "inv.producto.crear",
    "inv.producto.actualizar",
    "inv.unidad_medida.leer",
    "inv.unidad_medida.crear",
    "inv.unidad_medida.actualizar",
    "inv.almacen.leer",
    "inv.almacen.crear",
    "inv.almacen.actualizar",
    "inv.tipo_movimiento.leer",
    "inv.tipo_movimiento.crear",
    "inv.tipo_movimiento.actualizar",

    # INV stock
    "inv.stock.leer",
    "inv.stock.actualizar",

    # INV movimientos
    "inv.movimiento.leer",
    "inv.movimiento.crear",
    "inv.movimiento.actualizar",
    "inv.movimiento.procesar",
    "inv.movimiento.autorizar",
    "inv.movimiento.anular",

    # INV inventario físico
    "inv.inventario_fisico.leer",
    "inv.inventario_fisico.crear",
    "inv.inventario_fisico.actualizar",
    "inv.inventario_fisico.finalizar",
    "inv.inventario_fisico.aprobar",
    "inv.inventario_fisico.anular",
)

MANAGER_STANDARD_ROLE_NOT_FOUND = "MANAGER_STANDARD_ROLE_NOT_FOUND"
MANAGER_STANDARD_MISSING_PERMISO = "MANAGER_STANDARD_MISSING_PERMISO"
