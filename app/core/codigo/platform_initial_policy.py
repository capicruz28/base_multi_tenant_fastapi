"""Política inicial de filas cfg_codigo_secuencia sembradas por Platform.

Independiente de ``SequenceCatalog.policy`` (contrato F15A del catálogo).
Solo aplica al INSERT de provisioning (onboarding Shared/Dedicated y lazy creation).
El runtime sigue leyendo ``cfg_codigo_secuencia.generation_policy``.
"""

from __future__ import annotations

from app.core.codigo.enums import CodePolicy

__all__ = [
    "PLATFORM_INITIAL_GENERATION_POLICY",
    "platform_initial_generation_policy",
]

# Valor que Platform escribe al crear una fila nueva en cfg_codigo_secuencia.
PLATFORM_INITIAL_GENERATION_POLICY = CodePolicy.AUTO_REQUIRED


def platform_initial_generation_policy() -> CodePolicy:
    """Política inicial de provisioning Platform para filas CFG nuevas."""
    return PLATFORM_INITIAL_GENERATION_POLICY
