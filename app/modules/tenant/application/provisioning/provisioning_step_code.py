"""Códigos sanitizados de pasos saga S1–S10 expuestos al FE."""
from enum import StrEnum


class ProvisioningStepCode(StrEnum):
    REGISTRY = "registry"
    STORAGE_ALLOCATION = "storage_allocation"
    CREATE_DATABASE = "create_database"
    APPLY_SCHEMA_ERP = "apply_schema_erp"
    APPLY_SCHEMA_RBAC = "apply_schema_rbac"
    APPLY_CATALOGS = "apply_catalogs"
    SEED_TENANT = "seed_tenant"
    REGISTER_METADATA = "register_metadata"
    ACTIVATE_ROUTING = "activate_routing"
    MARK_READY = "mark_ready"


PROVISIONING_STEP_CODE_VALUES: frozenset[str] = frozenset(
    code.value for code in ProvisioningStepCode
)

SAGA_STEP_ORDER: tuple[ProvisioningStepCode, ...] = (
    ProvisioningStepCode.REGISTRY,
    ProvisioningStepCode.STORAGE_ALLOCATION,
    ProvisioningStepCode.CREATE_DATABASE,
    ProvisioningStepCode.APPLY_SCHEMA_ERP,
    ProvisioningStepCode.APPLY_SCHEMA_RBAC,
    ProvisioningStepCode.APPLY_CATALOGS,
    ProvisioningStepCode.SEED_TENANT,
    ProvisioningStepCode.REGISTER_METADATA,
    ProvisioningStepCode.ACTIVATE_ROUTING,
    ProvisioningStepCode.MARK_READY,
)

SAGA_ORDER_BY_CODE: dict[ProvisioningStepCode, int] = {
    code: index + 1 for index, code in enumerate(SAGA_STEP_ORDER)
}


def parse_provisioning_step_code(value: str) -> ProvisioningStepCode:
    try:
        return ProvisioningStepCode(value)
    except ValueError as exc:
        raise ValueError(
            f"step_code inválido: '{value}'. "
            f"Valores permitidos: {sorted(PROVISIONING_STEP_CODE_VALUES)}"
        ) from exc


__all__ = [
    "PROVISIONING_STEP_CODE_VALUES",
    "ProvisioningStepCode",
    "SAGA_ORDER_BY_CODE",
    "SAGA_STEP_ORDER",
    "parse_provisioning_step_code",
]
