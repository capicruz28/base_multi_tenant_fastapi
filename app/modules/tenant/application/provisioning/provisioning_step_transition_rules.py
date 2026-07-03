"""Reglas de transición por step saga — PR-F4-02."""
from __future__ import annotations

from app.core.exceptions import ValidationError
from app.modules.tenant.application.provisioning.provisioning_step_status import (
    ProvisioningStepStatus,
)

ALLOWED_STEP_STATUS_TRANSITIONS: dict[
    ProvisioningStepStatus, frozenset[ProvisioningStepStatus]
] = {
    ProvisioningStepStatus.PENDING: frozenset(
        {ProvisioningStepStatus.RUNNING, ProvisioningStepStatus.SKIPPED}
    ),
    ProvisioningStepStatus.RUNNING: frozenset(
        {ProvisioningStepStatus.COMPLETED, ProvisioningStepStatus.FAILED}
    ),
    ProvisioningStepStatus.FAILED: frozenset({ProvisioningStepStatus.RUNNING}),
    ProvisioningStepStatus.COMPLETED: frozenset(),
    ProvisioningStepStatus.SKIPPED: frozenset(),
}


def assert_step_status_transition(
    current: ProvisioningStepStatus,
    target: ProvisioningStepStatus,
) -> None:
    if current == target:
        raise ValidationError(
            detail=(
                f"Transición idempotente no permitida en step: "
                f"estado ya es '{target.value}'."
            ),
            internal_code="PROVISIONING_STEP_NOOP",
        )

    allowed = ALLOWED_STEP_STATUS_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValidationError(
            detail=(
                f"Transición step_status no permitida: "
                f"'{current.value}' → '{target.value}'."
            ),
            internal_code="INVALID_STEP_STATUS_TRANSITION",
        )


__all__ = [
    "ALLOWED_STEP_STATUS_TRANSITIONS",
    "assert_step_status_transition",
]
