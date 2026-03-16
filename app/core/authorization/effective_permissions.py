# app/core/authorization/effective_permissions.py
"""
DTO EffectivePermissions para el Permission Resolver (Stage 1).

Representa los permisos efectivos de un usuario en un tenant.
Serializable a JSON para cache; expone .codes para plug-and-play con build_user_with_roles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Literal
from uuid import UUID


SourceType = Literal["cache", "database", "super_admin"]


@dataclass(frozen=True)
class EffectivePermissions:
    """
    Permisos efectivos resueltos para (usuario_id, cliente_id).
    Inmutable; serializable para cache.
    """
    codes: List[str]
    is_super_admin: bool
    cliente_id: UUID
    usuario_id: UUID
    active_module_codes: Optional[List[str]] = None
    source: Optional[SourceType] = None

    def to_dict(self) -> dict:
        """Serialización para cache (JSON-compatible)."""
        return {
            "codes": list(self.codes),
            "is_super_admin": self.is_super_admin,
            "cliente_id": str(self.cliente_id),
            "usuario_id": str(self.usuario_id),
            "active_module_codes": self.active_module_codes,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> EffectivePermissions:
        """Deserialización desde cache."""
        return cls(
            codes=list(data.get("codes", []) or []),
            is_super_admin=bool(data.get("is_super_admin", False)),
            cliente_id=UUID(data["cliente_id"]) if isinstance(data.get("cliente_id"), str) else data["cliente_id"],
            usuario_id=UUID(data["usuario_id"]) if isinstance(data.get("usuario_id"), str) else data["usuario_id"],
            active_module_codes=data.get("active_module_codes"),
            source=data.get("source"),
        )
