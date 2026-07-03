"""F6-P1 — contexto mínimo para operaciones Identity Gateway."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class IdentityContext:
    """Tenant operativo para lecturas/escrituras de identidad."""

    cliente_id: UUID


__all__ = ["IdentityContext"]
