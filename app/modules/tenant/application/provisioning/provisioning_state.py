"""Estados oficiales del ciclo de vida Dedicated provisioning (CP)."""
from enum import StrEnum


class ProvisioningState(StrEnum):
    """Contrato público v1 — DEDICATED_PROVISIONING_API_CONTRACT §7."""

    PROVISIONING = "provisioning"
    READY = "ready"
    FAILED = "failed"


PROVISIONING_STATE_VALUES: frozenset[str] = frozenset(
    state.value for state in ProvisioningState
)

TERMINAL_PROVISIONING_STATES: frozenset[ProvisioningState] = frozenset(
    {ProvisioningState.READY, ProvisioningState.FAILED}
)

NON_TERMINAL_PROVISIONING_STATES: frozenset[ProvisioningState] = frozenset(
    {ProvisioningState.PROVISIONING}
)


def parse_provisioning_state(value: str) -> ProvisioningState:
    try:
        return ProvisioningState(value)
    except ValueError as exc:
        raise ValueError(
            f"provisioning_state inválido: '{value}'. "
            f"Valores permitidos: {sorted(PROVISIONING_STATE_VALUES)}"
        ) from exc


__all__ = [
    "NON_TERMINAL_PROVISIONING_STATES",
    "PROVISIONING_STATE_VALUES",
    "ProvisioningState",
    "TERMINAL_PROVISIONING_STATES",
    "parse_provisioning_state",
]
