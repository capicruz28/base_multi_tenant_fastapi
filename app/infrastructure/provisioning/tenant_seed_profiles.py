"""Perfiles seed tenant Dedicated — PR-F4-07 / ADR-F4-02 / BL-F4 §12 S7."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Sequence

from app.core.codigo.onboarding_seed import EAGER_SEQUENCE_KEYS
from app.core.exceptions import ValidationError
from app.infrastructure.provisioning.catalog_profiles import normalize_plan_suscripcion

TENANT_SEED_PROFILE_VERSION = "1.0.0"
_STEP_CODE = "seed_tenant"


@dataclass(frozen=True, slots=True)
class TenantSeedStepDefinition:
    step_code: str
    execution_order: int
    marker_code: str
    expected_marker_sha256: str


@dataclass(frozen=True, slots=True)
class TenantSeedProfile:
    profile_code: str
    plan_suscripcion: str
    version: str
    steps: tuple[TenantSeedStepDefinition, ...]
    row_expectations: tuple[tuple[str, int], ...]


def _marker_sha256(marker_code: str) -> str:
    payload = f"{marker_code}:{TENANT_SEED_PROFILE_VERSION}:{_STEP_CODE}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


_TENANT_SEED_STEPS: tuple[tuple[str, int], ...] = (
    ("seed_base_roles", 1),
    ("seed_org_empresa", 2),
    ("seed_admin_user", 3),
    ("seed_admin_empresa_link", 4),
    ("seed_tenant_rbac", 5),
    ("seed_codigo_secuencias", 6),
)


def _build_step_definitions() -> tuple[TenantSeedStepDefinition, ...]:
    steps: list[TenantSeedStepDefinition] = []
    for step_code, order in _TENANT_SEED_STEPS:
        marker_code = f"tenant_{step_code}_v1"
        steps.append(
            TenantSeedStepDefinition(
                step_code=step_code,
                execution_order=order,
                marker_code=marker_code,
                expected_marker_sha256=_marker_sha256(marker_code),
            )
        )
    return tuple(steps)


TENANT_SEED_STEP_DEFINITIONS = _build_step_definitions()


def resolve_tenant_seed_profile(
    plan_suscripcion: str | None,
) -> TenantSeedProfile:
    plan = normalize_plan_suscripcion(plan_suscripcion)
    return TenantSeedProfile(
        profile_code=f"dedicated_tenant_seed_{plan}_v1",
        plan_suscripcion=plan,
        version=TENANT_SEED_PROFILE_VERSION,
        steps=TENANT_SEED_STEP_DEFINITIONS,
        row_expectations=_row_expectations_for_profile(),
    )


def _row_expectations_for_profile() -> tuple[tuple[str, int], ...]:
    return (
        ("rol", 3),
        ("org_empresa", 1),
        ("usuario", 1),
        ("cfg_codigo_secuencia", len(EAGER_SEQUENCE_KEYS)),
    )


def validate_tenant_seed_profile_integrity(profile: TenantSeedProfile) -> None:
    if profile.version != TENANT_SEED_PROFILE_VERSION:
        raise ValidationError(
            detail="Versión de perfil tenant seed no soportada.",
            internal_code="TENANT_SEED_PROFILE_VERSION_UNSUPPORTED",
        )
    orders = [step.execution_order for step in profile.steps]
    if orders != sorted(orders) or len(set(orders)) != len(orders):
        raise ValidationError(
            detail="Orden de ejecución tenant seed inválido.",
            internal_code="TENANT_SEED_PROFILE_ORDER_INVALID",
        )
    known_codes = {item[0] for item in _TENANT_SEED_STEPS}
    for step in profile.steps:
        if step.step_code not in known_codes:
            raise ValidationError(
                detail=f"Paso tenant seed desconocido: {step.step_code}.",
                internal_code="TENANT_SEED_STEP_UNKNOWN",
            )
        if step.expected_marker_sha256 != _marker_sha256(step.marker_code):
            raise ValidationError(
                detail=f"Integridad marker inválida para {step.marker_code}.",
                internal_code="TENANT_SEED_PROFILE_INTEGRITY_FAILED",
            )


def dedupe_row_expectations(
    expectations: Sequence[tuple[str, int]],
) -> tuple[tuple[str, int], ...]:
    merged: dict[str, int] = {}
    for table_name, min_rows in expectations:
        merged[table_name] = max(merged.get(table_name, 0), min_rows)
    return tuple((table, merged[table]) for table in sorted(merged))


__all__ = [
    "TENANT_SEED_PROFILE_VERSION",
    "TenantSeedProfile",
    "TenantSeedStepDefinition",
    "dedupe_row_expectations",
    "resolve_tenant_seed_profile",
    "validate_tenant_seed_profile_integrity",
]
