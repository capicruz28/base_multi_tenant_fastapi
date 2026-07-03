"""PR-F4-06 — tests unitarios DedicatedCatalogSeedService."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, DatabaseError, ValidationError
from app.infrastructure.provisioning.catalog_profiles import (
    ALL_CATALOG_MODULE_CODES,
    resolve_catalog_seed_profile,
    validate_catalog_profile_integrity,
)
from app.infrastructure.provisioning.dedicated_catalog_seed_service import (
    DedicatedCatalogSeedService,
)
from app.infrastructure.provisioning.dedicated_catalog_seed_types import (
    DedicatedCatalogSeedRequest,
)

CLIENTE_ID = uuid4()

_INSERT_MARKER_RE = re.compile(
    r"INSERT INTO bootstrap_applied .*? VALUES \(N'([^']+)', N'[^']*', N'([^']+)', N'[^']+'\);",
    re.DOTALL,
)


class MockCatalogDdlClient:
    def __init__(self) -> None:
        self.executed: list[tuple[str, str]] = []
        self.markers: dict[str, str] = {}
        self.row_counts: dict[str, int] = {
            "modulo": 27,
            "permiso": 12,
            "cat_moneda": 0,
            "cat_pais": 0,
            "cat_departamento": 0,
            "cat_provincia": 0,
            "cat_distrito": 0,
        }
        self.fail_on_script_batch = False

    async def scalar_int(self, sql: str, *, database: str = "master") -> int | None:
        if "COUNT(*)" in sql:
            for table, count in self.row_counts.items():
                if f"[{table}]" in sql:
                    return count
        return None

    async def scalar_str(self, sql: str, *, database: str = "master") -> str | None:
        if "FROM bootstrap_applied" in sql:
            for code, checksum in self.markers.items():
                if f"N'{code}'" in sql:
                    return checksum
        return None

    async def execute(self, sql: str, *, database: str = "master") -> None:
        if self.fail_on_script_batch and "INSERT INTO bootstrap_applied" not in sql:
            raise DatabaseError(
                detail="Error ejecutando sentencia DDL de plataforma.",
                internal_code="DDL_EXECUTE_FAILED",
            )
        self.executed.append((database, sql))
        match = _INSERT_MARKER_RE.search(sql)
        if match:
            self.markers[match.group(1)] = match.group(2)


def _write_script(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _patch_catalog_checksums(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checksums = {
        "02_catalog/S010__seed_modulo_menu_completo.sql": _write_script(
            tmp_path / "02_catalog" / "S010__seed_modulo_menu_completo.sql",
            "INSERT INTO modulo VALUES (1);\n",
        ),
        "02_catalog/S020__seed_admin_menu.sql": _write_script(
            tmp_path / "02_catalog" / "S020__seed_admin_menu.sql",
            "INSERT INTO permiso VALUES (1);\n",
        ),
        "02_catalog/S030__seed_permisos_core.sql": _write_script(
            tmp_path / "02_catalog" / "S030__seed_permisos_core.sql",
            "INSERT INTO permiso VALUES (2);\n",
        ),
        "02_catalog/permisos_rbac/S040__permisos_rbac_org.sql": _write_script(
            tmp_path / "02_catalog" / "permisos_rbac" / "S040__permisos_rbac_org.sql",
            "INSERT INTO permiso VALUES (3);\n",
        ),
        "02_catalog/permisos_rbac/S041__permisos_rbac_inv-fase4.sql": _write_script(
            tmp_path
            / "02_catalog"
            / "permisos_rbac"
            / "S041__permisos_rbac_inv-fase4.sql",
            "INSERT INTO permiso VALUES (4);\n",
        ),
        "02_catalog/permisos_rbac/S042__permisos_rbac_inv-lifecycle.sql": _write_script(
            tmp_path
            / "02_catalog"
            / "permisos_rbac"
            / "S042__permisos_rbac_inv-lifecycle.sql",
            "INSERT INTO permiso VALUES (5);\n",
        ),
    }

    import app.infrastructure.provisioning.catalog_profiles as profiles_module

    merged = dict(profiles_module._CATALOG_CHECKSUMS)
    merged.update(checksums)
    monkeypatch.setattr(profiles_module, "_CATALOG_CHECKSUMS", merged)
    monkeypatch.setattr(
        profiles_module,
        "CATALOG_SCRIPT_REGISTRY",
        profiles_module._build_catalog_registry(),
    )


@pytest.fixture
def ddl_client() -> MockCatalogDdlClient:
    return MockCatalogDdlClient()


@pytest.fixture
def patched_catalog(
    tmp_path: Path,
    ddl_client: MockCatalogDdlClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.core.config.settings.DEDICATED_PERMISSION_CATALOG_SYNC_ENABLED",
        False,
    )
    _patch_catalog_checksums(tmp_path, monkeypatch)
    service = DedicatedCatalogSeedService(
        ddl_client=ddl_client,
        bootstrap_root=tmp_path,
    )
    return service


@pytest.mark.unit
def test_f4_06_trial_profile_resolves_base_and_module_scripts():
    profile = resolve_catalog_seed_profile("trial")
    codes = [entry.script_code for entry in profile.scripts]
    assert codes[:3] == ["catalog_s010", "catalog_s020", "catalog_s030"]
    assert "catalog_s040" in codes
    assert "catalog_s041" in codes
    assert "catalog_s042" in codes
    assert "catalog_s043" not in codes


@pytest.mark.unit
def test_f4_06_enterprise_profile_includes_all_module_scripts():
    profile = resolve_catalog_seed_profile("enterprise")
    assert profile.module_codes == ALL_CATALOG_MODULE_CODES
    assert profile.scripts[-1].script_code == "catalog_s066"
    assert len(profile.scripts) == 30


@pytest.mark.unit
def test_f4_06_validate_catalog_profile_integrity_real_bootstrap_v2():
    profile = resolve_catalog_seed_profile("trial")
    validate_catalog_profile_integrity(profile)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_06_run_executes_trial_catalog_scripts_in_order(
    patched_catalog: DedicatedCatalogSeedService,
    ddl_client: MockCatalogDdlClient,
):
    request = DedicatedCatalogSeedRequest(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
        plan_suscripcion="trial",
    )
    result = await patched_catalog.run_catalog_seed(request)

    assert result.profile_code == "dedicated_catalog_trial_v1"
    assert result.scripts_executed == (
        "catalog_s010",
        "catalog_s020",
        "catalog_s030",
        "catalog_s040",
        "catalog_s041",
        "catalog_s042",
    )
    assert result.scripts_skipped == ()
    assert result.batches_executed == 6
    assert any(v.table_name == "modulo" and v.row_count == 27 for v in result.row_verifications)
    assert any(v.table_name == "cat_pais" for v in result.row_verifications)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_06_rerun_is_idempotent(
    patched_catalog: DedicatedCatalogSeedService,
    ddl_client: MockCatalogDdlClient,
):
    request = DedicatedCatalogSeedRequest(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
        plan_suscripcion="trial",
    )
    first = await patched_catalog.run_catalog_seed(request)
    executed_after_first = len(ddl_client.executed)
    second = await patched_catalog.run_catalog_seed(request)

    assert first.scripts_executed == (
        "catalog_s010",
        "catalog_s020",
        "catalog_s030",
        "catalog_s040",
        "catalog_s041",
        "catalog_s042",
    )
    assert second.scripts_executed == ()
    assert second.scripts_skipped == first.scripts_executed
    new_executions = ddl_client.executed[executed_after_first:]
    assert not any("INSERT INTO permiso" in sql for _, sql in new_executions)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_06_marker_checksum_mismatch_raises_conflict(
    patched_catalog: DedicatedCatalogSeedService,
    ddl_client: MockCatalogDdlClient,
):
    ddl_client.markers["catalog_s010"] = "deadbeef" * 8
    request = DedicatedCatalogSeedRequest(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
        plan_suscripcion="trial",
    )
    with pytest.raises(ConflictError) as exc:
        await patched_catalog.run_catalog_seed(request)
    assert exc.value.internal_code == "CATALOG_MARKER_CHECKSUM_MISMATCH"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_06_sql_failure_maps_to_provisioning_catalog_failed(
    patched_catalog: DedicatedCatalogSeedService,
    ddl_client: MockCatalogDdlClient,
):
    ddl_client.fail_on_script_batch = True
    request = DedicatedCatalogSeedRequest(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
        plan_suscripcion="trial",
    )
    with pytest.raises(ConflictError) as exc:
        await patched_catalog.run_catalog_seed(request)
    assert exc.value.internal_code == "PROVISIONING_CATALOG_FAILED"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_06_row_count_failure(
    patched_catalog: DedicatedCatalogSeedService,
    ddl_client: MockCatalogDdlClient,
):
    ddl_client.row_counts["modulo"] = 0
    request = DedicatedCatalogSeedRequest(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
        plan_suscripcion="trial",
    )
    with pytest.raises(ConflictError) as exc:
        await patched_catalog.run_catalog_seed(request)
    assert exc.value.internal_code == "CATALOG_ROW_COUNT_FAILED"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_06_default_client_disabled_without_injection():
    service = DedicatedCatalogSeedService()
    request = DedicatedCatalogSeedRequest(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
    )
    with pytest.raises(ValidationError) as exc:
        await service.run_catalog_seed(request)
    assert exc.value.internal_code == "PROVISIONING_DDL_EXECUTOR_DISABLED"


@pytest.mark.unit
def test_f4_06_catalog_integrity_fails_on_checksum_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _patch_catalog_checksums(tmp_path, monkeypatch)
    profile = resolve_catalog_seed_profile("trial")
    script_path = tmp_path / profile.scripts[0].relative_path
    script_path.write_text("-- mutated\n", encoding="utf-8")
    with pytest.raises(ValidationError) as exc:
        validate_catalog_profile_integrity(profile, bootstrap_root=tmp_path)
    assert exc.value.internal_code == "CATALOG_PROFILE_INTEGRITY_FAILED"
