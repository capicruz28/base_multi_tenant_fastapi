"""
T1 — BASE_OPERATIVE: permisos transversales para roles operativos (MANAGER/USER).

Referencia: app/docs/auditoria/ROLE_BUNDLE_BASELINE_AUDIT.md

Nota: no importar core_permissions aquí (evita ciclo al ejecutar scripts repair).
"""
from __future__ import annotations

MANAGER_ROL_CODIGO = "MANAGER_TENANT"
USER_ROL_CODIGO = "USER_TENANT"

OPERATIVE_ROLE_CODIGOS: tuple[str, ...] = (MANAGER_ROL_CODIGO, USER_ROL_CODIGO)

CORE_APP_ACCEDER = "core.app.acceder"

BASE_OPERATIVE_PERMISSION_CODIGOS: tuple[str, ...] = (
    CORE_APP_ACCEDER,
    "tenant.branding.leer",
    "org.empresa.leer",
)

BASE_OPERATIVE_MISSING_PERMISO = "BASE_OPERATIVE_MISSING_PERMISO"
BASE_OPERATIVE_ROLE_NOT_FOUND = "BASE_OPERATIVE_ROLE_NOT_FOUND"
