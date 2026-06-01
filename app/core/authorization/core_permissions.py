# app/core/authorization/core_permissions.py
"""
Permisos estáticos del sistema (grant-only) no declarados en rutas HTTP.
Se registran en PermissionRegistry antes del sync de startup.
"""
from __future__ import annotations

from app.core.authorization.permission_metadata import PermissionMetadata
from app.core.authorization.permission_registry import register

CORE_APP_ACCEDER = "core.app.acceder"
ADMIN_PLATFORM_ACCESS = "admin.platform.access"

# Nunca desactivar por permission_sync aunque no aparezcan en rutas.
PROTECTED_PERMISSION_CODIGOS: frozenset[str] = frozenset(
    {CORE_APP_ACCEDER, ADMIN_PLATFORM_ACCESS}
)

CORE_STATIC_PERMISSIONS: list[PermissionMetadata] = [
    {
        "codigo": CORE_APP_ACCEDER,
        "nombre": "Acceder a la aplicación",
        "descripcion": "Permite iniciar sesión y acceder al sistema ERP",
        "recurso": "app",
        "accion": "acceder",
        "modulo_codigo": None,
    },
    {
        "codigo": ADMIN_PLATFORM_ACCESS,
        "nombre": "Acceso a Administración de Plataforma",
        "descripcion": "Permite acceder a las pantallas de administración global",
        "recurso": "admin.platform",
        "accion": "acceder",
        "modulo_codigo": "SYS_ADMIN",
    },
]


def register_core_permissions() -> None:
    """Idempotente: registra permisos core en PermissionRegistry."""
    for meta in CORE_STATIC_PERMISSIONS:
        register(meta)
