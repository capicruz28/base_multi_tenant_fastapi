"""
T3 — USER_STANDARD: bundle estándar para USER_TENANT.

Incluye:
- rol_permiso (API RBAC)
- rol_menu_permiso (visibilidad UI de /auth/menu)

Restricciones funcionales aprobadas:
- Predominantemente lectura: solo *.leer (además de BASE_OPERATIVE)
- No crear / no editar / no eliminar registros
- Excluir SYS_ADMIN / PLATFORM / CATALOGOS / administración tenant
- Excluir administración de empresas (empresa queda solo lectura por BASE_OPERATIVE)
"""

from __future__ import annotations

from uuid import UUID

USER_ROL_CODIGO = "USER_TENANT"

# Menús ORG/INV visibles para user estándar (sin Kardex).
# Fuente: catálogo central modulo_menu (ver docs/auditoria/USER_STANDARD_BUNDLE_DESIGN.md)
USER_STANDARD_MENU_GRANTS: tuple[tuple[UUID, dict], ...] = (
    # ORG (lectura)
    (UUID("E3010001-0000-4000-8000-000000000001"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # ORG_MI_EMPRESA
    (UUID("E3010002-0000-4000-8000-000000000002"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # ORG_SUCURSALES
    (UUID("E3010003-0000-4000-8000-000000000003"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # ORG_DEPARTAMENTOS
    (UUID("E3010004-0000-4000-8000-000000000004"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # ORG_CARGOS
    (UUID("E3010005-0000-4000-8000-000000000005"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # ORG_CENTROS_COSTO
    (UUID("E3010006-0000-4000-8000-000000000006"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # ORG_PARAMETROS

    # INV (lectura)
    (UUID("E3020002-0000-4000-8000-000000000001"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_CATEGORIAS
    (UUID("E3020001-0000-4000-8000-000000000002"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_PRODUCTOS
    (UUID("E3020003-0000-4000-8000-000000000003"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_UNIDADES
    (UUID("E3020004-0000-4000-8000-000000000004"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_ALMACENES
    (UUID("E3020005-0000-4000-8000-000000000005"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_STOCK
    (UUID("E3020006-0000-4000-8000-000000000006"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_TIPOS_MOV
    (UUID("E3020007-0000-4000-8000-000000000007"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_MOVIMIENTOS
    (UUID("E3020008-0000-4000-8000-000000000008"), {"ver": 1, "crear": 0, "editar": 0, "eliminar": 0, "exportar": 1, "imprimir": 0, "aprobar": 0}),  # INV_INV_FISICO
)

# Permisos API para USER_STANDARD (16 códigos).
# Incluye BASE_OPERATIVE y permisos ORG/INV solo lectura.
USER_STANDARD_PERMISSION_CODIGOS: tuple[str, ...] = (
    # BASE_OPERATIVE (T1)
    "core.app.acceder",
    "tenant.branding.leer",
    "org.empresa.leer",

    # ORG lectura
    "org.sucursal.leer",
    "org.departamento.leer",
    "org.cargo.leer",
    "org.centro_costo.leer",
    "org.parametro.leer",

    # INV lectura
    "inv.categoria.leer",
    "inv.producto.leer",
    "inv.unidad_medida.leer",
    "inv.almacen.leer",
    "inv.stock.leer",
    "inv.tipo_movimiento.leer",
    "inv.movimiento.leer",
    "inv.inventario_fisico.leer",
)

USER_STANDARD_ROLE_NOT_FOUND = "USER_STANDARD_ROLE_NOT_FOUND"
USER_STANDARD_MISSING_PERMISO = "USER_STANDARD_MISSING_PERMISO"

