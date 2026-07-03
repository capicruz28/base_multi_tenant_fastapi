"""Contexto efímero saga provisioning — solo memoria (PR-F4-08 / C-01)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class ProvisioningSagaEphemeralContext:
    """
    Secretos y datos no persistibles en CP.

    Transportado únicamente en el primer dispatch post-``POST /clientes/``.
    """

    admin_password: str
    app_login_password: Optional[str] = None


__all__ = ["ProvisioningSagaEphemeralContext"]
