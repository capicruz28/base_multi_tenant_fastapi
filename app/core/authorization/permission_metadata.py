# app/core/authorization/permission_metadata.py
"""
Metadata para permisos RBAC code-first.
Usado por @RequirePermission y PermissionSyncService para sincronizar con tabla permiso.
"""
from typing import TypedDict, Optional


class PermissionMetadata(TypedDict, total=False):
    """Metadata declarada en código para un permiso de negocio."""
    codigo: str
    nombre: str
    descripcion: Optional[str]
    recurso: str
    accion: str
    modulo_codigo: Optional[str]
