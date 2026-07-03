"""Validaciones de consistencia perfil cliente ↔ provisioning state."""
from __future__ import annotations

from typing import Optional

from app.core.exceptions import ValidationError
from app.modules.tenant.application.provisioning.provisioning_state import (
    ProvisioningState,
)

DEDICATED_INSTALLATION_TYPE = "dedicated"
SHARED_INSTALLATION_TYPE = "shared"


def assert_cliente_provisioning_profile(
    *,
    tipo_instalacion: str,
    provisioning_state: Optional[str],
) -> None:
    """
    Reglas CP:
    - Shared: ``provisioning_state`` debe ser NULL.
    - Dedicated legacy: ``provisioning_state`` puede ser NULL.
    - Dedicated F4+: estados oficiales cuando presente.
    """
    if provisioning_state is None:
        return

    try:
        ProvisioningState(provisioning_state)
    except ValueError as exc:
        raise ValidationError(
            detail=f"provisioning_state inválido en cliente: '{provisioning_state}'.",
            internal_code="INVALID_CLIENTE_PROVISIONING_STATE",
        ) from exc

    if tipo_instalacion == SHARED_INSTALLATION_TYPE:
        raise ValidationError(
            detail=(
                "Los tenants shared no pueden tener provisioning_state. "
                "Use NULL para instalaciones shared."
            ),
            internal_code="SHARED_PROVISIONING_STATE_FORBIDDEN",
        )


def dedicated_requires_provisioning_state(
    *,
    tipo_instalacion: str,
    provisioning_state: Optional[str],
) -> bool:
    """Indica si un dedicated activo en flujo F4 debe tener estado distinto de NULL."""
    return (
        tipo_instalacion == DEDICATED_INSTALLATION_TYPE
        and provisioning_state is not None
    )


__all__ = [
    "DEDICATED_INSTALLATION_TYPE",
    "SHARED_INSTALLATION_TYPE",
    "assert_cliente_provisioning_profile",
    "dedicated_requires_provisioning_state",
]
