"""
Unit tests: detección y reglas de reparación legacy RBAC (sin BD).
"""
from __future__ import annotations

from uuid import uuid4

from app.shared.legacy_rbac_repair_rules import (
    MIN_ADMIN_ROL_PERMISO_HEALTHY,
    evaluate_repair_need,
)


def test_healthy_tenant_no_repair():
    needs, reasons, skipped, skip = evaluate_repair_need(
        cliente_modulo_count=2,
        modulos_codigos=["ORG", "SYS_ADMIN"],
        admin_rol_id=uuid4(),
        rol_permiso_admin_count=44,
        has_core_app_acceder=True,
    )
    assert needs is False
    assert reasons == []
    assert skipped is False


def test_incomplete_no_cliente_modulo_no_rol_permiso():
    needs, reasons, skipped, skip = evaluate_repair_need(
        cliente_modulo_count=0,
        modulos_codigos=[],
        admin_rol_id=uuid4(),
        rol_permiso_admin_count=0,
        has_core_app_acceder=False,
    )
    assert needs is True
    assert "NO_CLIENTE_MODULO" in reasons
    assert "NO_ROL_PERMISO_ADMIN" in reasons
    assert skipped is False


def test_missing_org_module_only():
    needs, reasons, _, _ = evaluate_repair_need(
        cliente_modulo_count=1,
        modulos_codigos=["SYS_ADMIN"],
        admin_rol_id=uuid4(),
        rol_permiso_admin_count=10,
        has_core_app_acceder=True,
    )
    assert needs is True
    assert any(r.startswith("MISSING_MODULOS:") for r in reasons)


def test_skip_without_admin_tenant_role():
    needs, reasons, skipped, skip = evaluate_repair_need(
        cliente_modulo_count=0,
        modulos_codigos=[],
        admin_rol_id=None,
        rol_permiso_admin_count=0,
        has_core_app_acceder=False,
    )
    assert needs is False
    assert skipped is True
    assert skip == "ADMIN_TENANT_MISSING"


def test_legacy_complete_bundle_skips_repair():
    needs, reasons, skipped, _ = evaluate_repair_need(
        cliente_modulo_count=3,
        modulos_codigos=["ORG", "SYS_ADMIN", "INV"],
        admin_rol_id=uuid4(),
        rol_permiso_admin_count=100,
        has_core_app_acceder=False,
    )
    assert needs is False
    assert reasons == []


def test_low_rol_permiso_count_triggers_repair():
    needs, reasons, _, _ = evaluate_repair_need(
        cliente_modulo_count=2,
        modulos_codigos=["ORG", "SYS_ADMIN"],
        admin_rol_id=uuid4(),
        rol_permiso_admin_count=MIN_ADMIN_ROL_PERMISO_HEALTHY - 1,
        has_core_app_acceder=True,
    )
    assert needs is True
    assert "LOW_ROL_PERMISO_ADMIN_COUNT" in reasons
