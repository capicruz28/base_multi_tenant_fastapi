"""Tipos de dominio Dedicated Provisioning — state model CP (PR-F4-01)."""
from app.modules.tenant.application.provisioning.provisioning_consistency import (
    DEDICATED_INSTALLATION_TYPE,
    SHARED_INSTALLATION_TYPE,
    assert_cliente_provisioning_profile,
    dedicated_requires_provisioning_state,
)
from app.modules.tenant.application.provisioning.provisioning_records import (
    ClienteProvisioningSnapshot,
    TenantProvisioningRunRecord,
    TenantProvisioningStepRecord,
)
from app.modules.tenant.application.provisioning.provisioning_state import (
    NON_TERMINAL_PROVISIONING_STATES,
    PROVISIONING_STATE_VALUES,
    TERMINAL_PROVISIONING_STATES,
    ProvisioningState,
    parse_provisioning_state,
)
from app.modules.tenant.application.provisioning.provisioning_step_code import (
    PROVISIONING_STEP_CODE_VALUES,
    SAGA_ORDER_BY_CODE,
    SAGA_STEP_ORDER,
    ProvisioningStepCode,
    parse_provisioning_step_code,
)
from app.modules.tenant.application.provisioning.provisioning_step_status import (
    PROVISIONING_STEP_STATUS_VALUES,
    TERMINAL_STEP_STATUSES,
    ProvisioningStepStatus,
    parse_provisioning_step_status,
)
from app.modules.tenant.application.provisioning.provisioning_job_contracts import (
    ProvisioningJobDispatchResult,
    ProvisioningJobHandler,
    ProvisioningJobHandlerCallable,
    ProvisioningJobRequest,
)
from app.modules.tenant.application.provisioning.provisioning_state_result import (
    ProvisioningRunInitializedResult,
    ProvisioningStateTransitionResult,
    ProvisioningStepTransitionResult,
)
from app.modules.tenant.application.provisioning.provisioning_status_read import (
    DedicatedProvisioningStatusSnapshot,
    ProvisioningStepStatusRead,
)
from app.modules.tenant.application.provisioning.provisioning_step_transition_rules import (
    ALLOWED_STEP_STATUS_TRANSITIONS,
    assert_step_status_transition,
)
from app.modules.tenant.application.provisioning.provisioning_transition_rules import (
    ALLOWED_PROVISIONING_STATE_TRANSITIONS,
    assert_provisioning_state_transition,
    is_provisioning_state_terminal,
)

__all__ = [
    "ALLOWED_PROVISIONING_STATE_TRANSITIONS",
    "DEDICATED_INSTALLATION_TYPE",
    "NON_TERMINAL_PROVISIONING_STATES",
    "PROVISIONING_STATE_VALUES",
    "PROVISIONING_STEP_CODE_VALUES",
    "PROVISIONING_STEP_STATUS_VALUES",
    "SHARED_INSTALLATION_TYPE",
    "SAGA_ORDER_BY_CODE",
    "SAGA_STEP_ORDER",
    "TERMINAL_PROVISIONING_STATES",
    "TERMINAL_STEP_STATUSES",
    "ClienteProvisioningSnapshot",
    "ProvisioningState",
    "ProvisioningStepCode",
    "ProvisioningStepStatus",
    "TenantProvisioningRunRecord",
    "TenantProvisioningStepRecord",
    "assert_cliente_provisioning_profile",
    "assert_provisioning_state_transition",
    "assert_step_status_transition",
    "dedicated_requires_provisioning_state",
    "is_provisioning_state_terminal",
    "parse_provisioning_state",
    "parse_provisioning_step_code",
    "parse_provisioning_step_status",
    "ALLOWED_STEP_STATUS_TRANSITIONS",
    "DedicatedProvisioningStatusSnapshot",
    "ProvisioningStepStatusRead",
    "ProvisioningJobDispatchResult",
    "ProvisioningJobHandler",
    "ProvisioningJobHandlerCallable",
    "ProvisioningJobRequest",
    "ProvisioningSagaEphemeralContext",
    "ProvisioningRunInitializedResult",
    "ProvisioningStateTransitionResult",
    "ProvisioningStepTransitionResult",
]
