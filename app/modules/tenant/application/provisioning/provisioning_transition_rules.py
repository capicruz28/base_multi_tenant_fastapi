"""Reglas de transición del state model — sin orquestación (PR-F4-01)."""
from __future__ import annotations

from app.core.exceptions import ValidationError
from app.modules.tenant.application.provisioning.provisioning_state import (
    ProvisioningState,
)

ALLOWED_PROVISIONING_STATE_TRANSITIONS: dict[
    ProvisioningState, frozenset[ProvisioningState]
] = {
    ProvisioningState.PROVISIONING: frozenset(
        {ProvisioningState.READY, ProvisioningState.FAILED}
    ),
    ProvisioningState.FAILED: frozenset({ProvisioningState.PROVISIONING}),
    ProvisioningState.READY: frozenset(),
}


def assert_provisioning_state_transition(
    current: ProvisioningState | None,
    target: ProvisioningState,
) -> None:
    """
    Valida transición de estado provisioning.

    ``current=None`` representa alta inicial Dedicated → provisioning.
    """
    if current is None:
        if target != ProvisioningState.PROVISIONING:
            raise ValidationError(
                detail=(
                    "El estado inicial de provisioning debe ser 'provisioning'. "
                    f"Estado solicitado: '{target.value}'."
                ),
                internal_code="INVALID_INITIAL_PROVISIONING_STATE",
            )
        return

    if current == target:
        raise ValidationError(
            detail=(
                f"Transición idempotente no permitida: provisioning_state "
                f"ya es '{target.value}'."
            ),
            internal_code="PROVISIONING_STATE_NOOP",
        )

    allowed = ALLOWED_PROVISIONING_STATE_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValidationError(
            detail=(
                f"Transición provisioning_state no permitida: "
                f"'{current.value}' → '{target.value}'."
            ),
            internal_code="INVALID_PROVISIONING_STATE_TRANSITION",
        )


def is_provisioning_state_terminal(state: ProvisioningState) -> bool:
    return state == ProvisioningState.READY or state == ProvisioningState.FAILED


__all__ = [
    "ALLOWED_PROVISIONING_STATE_TRANSITIONS",
    "assert_provisioning_state_transition",
    "is_provisioning_state_terminal",
]
