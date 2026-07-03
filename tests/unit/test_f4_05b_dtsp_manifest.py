"""PR-F4-05b — tests unitarios DTSP manifest y script."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.infrastructure.provisioning.script_manifest import (
    BOOTSTRAP_V2_ROOT,
    DEDICATED_SCHEMA_MANIFEST_V2,
    DTSP_REQUIRED_TABLES,
    compute_file_sha256,
    load_dedicated_schema_manifest,
    validate_manifest_integrity,
)

_DTSP_RELATIVE = "05_dedicated/V020__tenant_identity_rbac_store.sql"


@pytest.mark.unit
def test_f4_05b_default_profile_is_v2():
    manifest = load_dedicated_schema_manifest()
    assert manifest.profile == "dedicated_schema_v2"
    assert len(manifest.entries) == 4


@pytest.mark.unit
def test_f4_05b_dtsp_entry_in_manifest():
    manifest = load_dedicated_schema_manifest()
    dtsp_entries = [
        entry
        for entry in manifest.entries
        if entry.script_code == "apply_schema_tenant_store_v020"
    ]
    assert len(dtsp_entries) == 1
    entry = dtsp_entries[0]
    assert entry.relative_path == _DTSP_RELATIVE
    assert entry.step_code == "apply_schema_rbac"
    assert entry.execution_order == 2


@pytest.mark.unit
def test_f4_05b_dtsp_script_checksum_frozen():
    manifest = load_dedicated_schema_manifest()
    dtsp_entry = next(
        entry
        for entry in manifest.entries
        if entry.script_code == "apply_schema_tenant_store_v020"
    )
    script_path = BOOTSTRAP_V2_ROOT / dtsp_entry.relative_path
    assert script_path.is_file()
    assert compute_file_sha256(script_path) == dtsp_entry.expected_sha256


@pytest.mark.unit
def test_f4_05b_manifest_integrity_includes_dtsp():
    validate_manifest_integrity(DEDICATED_SCHEMA_MANIFEST_V2)


@pytest.mark.unit
def test_f4_05b_dtsp_required_tables_count():
    assert len(DTSP_REQUIRED_TABLES) == 9


@pytest.mark.unit
def test_f4_05b_dtsp_sql_no_fk_to_cliente():
    sql = (BOOTSTRAP_V2_ROOT / _DTSP_RELATIVE).read_text(encoding="utf-8").lower()
    assert "references cliente(" not in sql
    assert "references dbo.cliente" not in sql


@pytest.mark.unit
def test_f4_05b_dtsp_sql_idempotent_pattern():
    sql = (BOOTSTRAP_V2_ROOT / _DTSP_RELATIVE).read_text(encoding="utf-8")
    for table in sorted(DTSP_REQUIRED_TABLES):
        assert f"name = N'{table}'" in sql


@pytest.mark.unit
def test_f4_05b_dtsp_script_exists_and_non_empty():
    path = Path(BOOTSTRAP_V2_ROOT) / _DTSP_RELATIVE
    assert path.stat().st_size > 0
