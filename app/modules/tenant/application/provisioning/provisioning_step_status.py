"""Estados de ejecución por paso saga."""
from enum import StrEnum


class ProvisioningStepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


PROVISIONING_STEP_STATUS_VALUES: frozenset[str] = frozenset(
    status.value for status in ProvisioningStepStatus
)

TERMINAL_STEP_STATUSES: frozenset[ProvisioningStepStatus] = frozenset(
    {
        ProvisioningStepStatus.COMPLETED,
        ProvisioningStepStatus.FAILED,
        ProvisioningStepStatus.SKIPPED,
    }
)


def parse_provisioning_step_status(value: str) -> ProvisioningStepStatus:
    try:
        return ProvisioningStepStatus(value)
    except ValueError as exc:
        raise ValueError(
            f"step_status inválido: '{value}'. "
            f"Valores permitidos: {sorted(PROVISIONING_STEP_STATUS_VALUES)}"
        ) from exc


__all__ = [
    "PROVISIONING_STEP_STATUS_VALUES",
    "ProvisioningStepStatus",
    "TERMINAL_STEP_STATUSES",
    "parse_provisioning_step_status",
]
