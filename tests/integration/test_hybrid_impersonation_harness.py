"""
PR-F0-04 — Hybrid impersonation harness tests.

Assert RD-05 / RI-18 vía harness (PR-F0-01). Sin BD, sin HTTP, sin fix AR-C05.

Patrón ORG/INV para datos ERP: require_session_cliente_id() — no current_user.cliente_id
del operador SYSTEM bajo impersonation (gap AR-C05 en módulos sin {cod}_deps no se corrige aquí).
"""
from __future__ import annotations

from uuid import UUID

from app.core.auth.impersonation import impersonation_effective_level_info
from app.core.tenant.session_scope import (
    SessionClienteResolution,
    require_session_cliente_id,
    resolve_session_cliente_id,
)
from tests.integration.helpers.hybrid_mock_metadata import HYBRID_FIXTURE_TENANT_SHARED

pytest_plugins = ("tests.integration.conftest_hybrid",)

SYSTEM_OPERATOR_CLIENTE_ID = UUID("00000000-0000-0000-0000-000000000001")


def _hybrid_impersonation_payload(*, target_cliente_id: UUID) -> dict:
    """JWT mock local — sin firma, sin Redis."""
    return {
        "sub": "platform_operator",
        "cliente_id": str(target_cliente_id),
        "is_impersonation": True,
        "effective_scope": "tenant",
        **impersonation_effective_level_info(),
    }


class ImpersonationContextViolation(AssertionError):
    """
    Violación del contrato de impersonation Hybrid.

    Especificación funcional normativa — no replica session_scope.py:
    - RD-05: tenant operativo desde JWT target, no fila SYSTEM del operador
    - RI-18: impersonation establece tenant operativo JWT target
    - G-08: aislamiento de dominio bajo impersonation
    """


def assert_impersonation_resolution_compliant(
    resolution: SessionClienteResolution,
    *,
    expected_target: UUID,
    operator_row: UUID,
) -> None:
    """
    Valida resolución bajo impersonation tenant-effective (spec RD-05 / RI-18).
    """
    if resolution.cliente_id != expected_target:
        raise ImpersonationContextViolation(
            f"RD-05: se esperaba tenant operativo {expected_target}, "
            f"obtenido {resolution.cliente_id}"
        )
    if resolution.source != "jwt_impersonation":
        raise ImpersonationContextViolation(
            f"RD-05: impersonation tenant-effective requiere source=jwt_impersonation, "
            f"obtenido {resolution.source}"
        )
    if resolution.cliente_id == operator_row and operator_row != expected_target:
        raise ImpersonationContextViolation(
            f"RI-18: tenant operativo no debe ser la fila SYSTEM del operador ({operator_row})"
        )


class TestHybridImpersonationRd05:
    """S1 — JWT target tenant (RD-05 / RI-18) con UUIDs harness F0-01."""

    def test_resolve_session_cliente_id_uses_jwt_target_harness_uuid(self) -> None:
        payload = _hybrid_impersonation_payload(
            target_cliente_id=HYBRID_FIXTURE_TENANT_SHARED,
        )
        resolution = resolve_session_cliente_id(
            payload=payload,
            user_cliente_id=SYSTEM_OPERATOR_CLIENTE_ID,
            request_cliente_id=SYSTEM_OPERATOR_CLIENTE_ID,
        )
        assert resolution.cliente_id == HYBRID_FIXTURE_TENANT_SHARED
        assert resolution.source == "jwt_impersonation"
        assert resolution.is_impersonation is True
        assert_impersonation_resolution_compliant(
            resolution,
            expected_target=HYBRID_FIXTURE_TENANT_SHARED,
            operator_row=SYSTEM_OPERATOR_CLIENTE_ID,
        )


class TestHybridImpersonationOperatorRowRejected:
    """S2 — operador SYSTEM no es tenant operativo de datos."""

    def test_resolution_does_not_use_operator_user_row(self) -> None:
        payload = _hybrid_impersonation_payload(
            target_cliente_id=HYBRID_FIXTURE_TENANT_SHARED,
        )
        resolution = resolve_session_cliente_id(
            payload=payload,
            user_cliente_id=SYSTEM_OPERATOR_CLIENTE_ID,
            request_cliente_id=SYSTEM_OPERATOR_CLIENTE_ID,
        )
        assert resolution.cliente_id != SYSTEM_OPERATOR_CLIENTE_ID
        assert_impersonation_resolution_compliant(
            resolution,
            expected_target=HYBRID_FIXTURE_TENANT_SHARED,
            operator_row=SYSTEM_OPERATOR_CLIENTE_ID,
        )


class TestHybridImpersonationDepsPattern:
    """S3 — require_session_cliente_id (patrón ORG/INV deps)."""

    def test_require_session_cliente_id_matches_jwt_target(self) -> None:
        payload = _hybrid_impersonation_payload(
            target_cliente_id=HYBRID_FIXTURE_TENANT_SHARED,
        )
        resolved = require_session_cliente_id(
            payload=payload,
            user_cliente_id=SYSTEM_OPERATOR_CLIENTE_ID,
            request_cliente_id=SYSTEM_OPERATOR_CLIENTE_ID,
        )
        assert resolved == HYBRID_FIXTURE_TENANT_SHARED


class TestHybridNonImpersonationControl:
    """S4 — contraste legacy: request_tenant sin impersonation."""

    def test_non_impersonation_uses_request_cliente_id(self) -> None:
        resolution = resolve_session_cliente_id(
            payload={"sub": "tenant_admin", "cliente_id": str(HYBRID_FIXTURE_TENANT_SHARED)},
            user_cliente_id=SYSTEM_OPERATOR_CLIENTE_ID,
            request_cliente_id=HYBRID_FIXTURE_TENANT_SHARED,
        )
        assert resolution.cliente_id == HYBRID_FIXTURE_TENANT_SHARED
        assert resolution.source == "request_tenant"
        assert resolution.is_impersonation is False
