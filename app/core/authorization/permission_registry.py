# app/core/authorization/permission_registry.py
"""
Registry global de permisos declarados en código (code-first).
Cada RequirePermission(metadata) registra aquí.
Única fuente en memoria para PermissionSyncService.
"""
from __future__ import annotations

import logging
from typing import Dict, List

from app.core.authorization.permission_metadata import PermissionMetadata

logger = logging.getLogger(__name__)

_registry: Dict[str, PermissionMetadata] = {}


def register(metadata: PermissionMetadata) -> None:
    """Registra o actualiza un permiso por codigo. Idempotente."""
    codigo = metadata.get("codigo")
    if not codigo or not isinstance(codigo, str):
        logger.warning("[RBAC] Permission metadata sin 'codigo' válido, ignorado: %s", metadata)
        return
    codigo = codigo.strip()
    _registry[codigo] = {
        "codigo": codigo,
        "nombre": metadata.get("nombre") or codigo,
        "descripcion": metadata.get("descripcion"),
        "recurso": metadata.get("recurso") or "",
        "accion": metadata.get("accion") or "",
        "modulo_codigo": metadata.get("modulo_codigo"),
    }


def get_all() -> List[PermissionMetadata]:
    """Devuelve todos los permisos registrados (lista única por codigo)."""
    return list(_registry.values())


def get_by_codigo(codigo: str) -> PermissionMetadata | None:
    """Devuelve un permiso por codigo o None."""
    return _registry.get(codigo)


def clear() -> None:
    """Limpia el registry (útil para tests)."""
    _registry.clear()
