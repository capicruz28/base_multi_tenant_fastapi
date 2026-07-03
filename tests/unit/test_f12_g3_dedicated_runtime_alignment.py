"""F12-G3 — Dedicated runtime alignment (auth_audit_log + runtime gate)."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.infrastructure.provisioning.script_manifest import (
    BOOTSTRAP_V2_ROOT,
    DEDICATED_RUNTIME_EXTRA_TABLES,
    DEDICATED_RUNTIME_REQUIRED_TABLES,
    DTSP_REQUIRED_TABLES,
    compute_file_sha256,
    load_dedicated_schema_manifest,
    validate_manifest_integrity,
)

_AUTH_AUDIT_RELATIVE = "05_dedicated/V030__auth_audit_log_dedicated.sql"


@pytest.mark.unit
def test_f12_g3_manifest_includes_auth_audit_script():
    manifest = load_dedicated_schema_manifest()
    assert manifest.version == "2.1.0"
    audit_entries = [
        e for e in manifest.entries if e.script_code == "apply_schema_auth_audit_v030"
    ]
    assert len(audit_entries) == 1
    entry = audit_entries[0]
    assert entry.relative_path == _AUTH_AUDIT_RELATIVE
    assert entry.execution_order == 4
    assert entry.step_code == "apply_schema_rbac"


@pytest.mark.unit
def test_f12_g3_auth_audit_script_checksum_frozen():
    manifest = load_dedicated_schema_manifest()
    entry = next(
        e for e in manifest.entries if e.script_code == "apply_schema_auth_audit_v030"
    )
    script_path = BOOTSTRAP_V2_ROOT / entry.relative_path
    assert script_path.is_file()
    assert compute_file_sha256(script_path) == entry.expected_sha256


@pytest.mark.unit
def test_f12_g3_manifest_integrity():
    validate_manifest_integrity(load_dedicated_schema_manifest())


@pytest.mark.unit
def test_f12_g3_runtime_required_tables_superset():
    assert DTSP_REQUIRED_TABLES.issubset(DEDICATED_RUNTIME_REQUIRED_TABLES)
    assert "rol_permiso" in DEDICATED_RUNTIME_REQUIRED_TABLES
    assert "auth_audit_log" in DEDICATED_RUNTIME_REQUIRED_TABLES
    assert "cfg_codigo_secuencia" in DEDICATED_RUNTIME_REQUIRED_TABLES
    assert "org_empresa" in DEDICATED_RUNTIME_REQUIRED_TABLES
    assert DEDICATED_RUNTIME_EXTRA_TABLES == frozenset(
        {"auth_audit_log", "cfg_codigo_secuencia", "org_empresa"}
    )


@pytest.mark.unit
def test_f12_g3_auth_audit_sql_no_fk_to_cliente():
    sql = (BOOTSTRAP_V2_ROOT / _AUTH_AUDIT_RELATIVE).read_text(encoding="utf-8").lower()
    assert "references cliente(" not in sql
    assert "references dbo.cliente" not in sql


@pytest.mark.unit
def test_f12_g3_auth_audit_sql_idempotent_and_table_name():
    sql = (BOOTSTRAP_V2_ROOT / _AUTH_AUDIT_RELATIVE).read_text(encoding="utf-8")
    assert "name = N'auth_audit_log'" in sql
    assert "IF NOT EXISTS" in sql


@pytest.mark.unit
def test_f12_g3_runtime_required_excludes_session_store():
    forbidden = {"user_session", "token_family", "refresh_tokens", "log_sincronizacion_usuario"}
    assert forbidden.isdisjoint(DEDICATED_RUNTIME_REQUIRED_TABLES)


@pytest.mark.unit
def test_f12_g3_ordered_script_codes():
    from app.infrastructure.provisioning.script_manifest import ordered_script_codes

    codes = ordered_script_codes(load_dedicated_schema_manifest())
    assert codes == (
        "apply_schema_erp_v010",
        "apply_schema_tenant_store_v020",
        "apply_schema_rbac_v010",
        "apply_schema_auth_audit_v030",
    )
