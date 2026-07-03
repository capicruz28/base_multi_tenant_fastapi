"""PR-F4-05 — tests unitarios BootstrapScriptRunner."""

from __future__ import annotations



import hashlib

import re

from pathlib import Path

from uuid import uuid4



import pytest



from app.core.exceptions import ConflictError, DatabaseError, ValidationError

from app.infrastructure.provisioning.bootstrap_script_runner import (

    BootstrapScriptRunner,

)

from app.infrastructure.provisioning.bootstrap_script_types import (

    BootstrapScriptRunRequest,

)

from app.infrastructure.provisioning.script_manifest import (

    DEDICATED_SCHEMA_MANIFEST_V1,

    DEDICATED_SCHEMA_MANIFEST_V2,

    BootstrapScriptManifest,

    BootstrapScriptManifestEntry,

    compute_file_sha256,

    discover_manifest_entries,

    load_dedicated_schema_manifest,

    ordered_script_codes,

    split_sql_server_batches,

    validate_manifest_integrity,

)



CLIENTE_ID = uuid4()



_INSERT_MARKER_RE = re.compile(

    r"INSERT INTO bootstrap_applied .*? VALUES \(N'([^']+)', N'[^']*', N'([^']+)', N'[^']+'\);",

    re.DOTALL,

)





class MockBootstrapDdlClient:

    def __init__(self, *, dtsp_tables_exist: bool = True) -> None:

        self.executed: list[tuple[str, str]] = []

        self.markers: dict[str, str] = {}

        self.fail_on_script_batch = False

        self.tables_created = False

        self.dtsp_tables_exist = dtsp_tables_exist



    async def scalar_int(self, sql: str, *, database: str = "master") -> int | None:

        if "OBJECT_ID" in sql and "dbo." in sql:

            return 1 if self.dtsp_tables_exist else 0

        return None



    async def scalar_str(self, sql: str, *, database: str = "master") -> str | None:

        if "FROM bootstrap_applied" in sql and "script_code" in sql:

            for code, checksum in self.markers.items():

                if f"N'{code}'" in sql:

                    return checksum

        return None



    async def execute(self, sql: str, *, database: str = "master") -> None:

        if "CREATE TABLE bootstrap_applied" in sql:

            self.tables_created = True

        elif self.fail_on_script_batch and "INSERT INTO bootstrap_applied" not in sql:

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





def _build_temp_manifest_root(

    tmp_path: Path,

    *,

    profile: str = "dedicated_schema_v2",

) -> BootstrapScriptManifest:

    erp_sha = _write_script(

        tmp_path / "01_schema" / "V010__tablas_bd_erp_completo.sql",

        "CREATE TABLE demo_erp (id INT);\nGO\nSELECT 1;\n",

    )

    dtsp_sha = _write_script(

        tmp_path / "05_dedicated" / "V020__tenant_identity_rbac_store.sql",

        "CREATE TABLE modulo (id INT);\nGO\nCREATE TABLE usuario (id INT);\n",

    )

    rbac_sha = _write_script(

        tmp_path / "05_dedicated" / "V010__rbac_tablas_dedicated.sql",

        "IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'rol_permiso') SELECT 1;\n",

    )

    audit_sha = _write_script(

        tmp_path / "05_dedicated" / "V030__auth_audit_log_dedicated.sql",

        "IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'auth_audit_log') SELECT 1;\n",

    )

    if profile == "dedicated_schema_v1":

        return BootstrapScriptManifest(

            version="test-1.0.0",

            profile="dedicated_schema_v1",

            entries=(

                BootstrapScriptManifestEntry(

                    script_code="apply_schema_erp_v010",

                    relative_path="01_schema/V010__tablas_bd_erp_completo.sql",

                    step_code="apply_schema_erp",

                    execution_order=1,

                    expected_sha256=erp_sha,

                ),

                BootstrapScriptManifestEntry(

                    script_code="apply_schema_rbac_v010",

                    relative_path="05_dedicated/V010__rbac_tablas_dedicated.sql",

                    step_code="apply_schema_rbac",

                    execution_order=2,

                    expected_sha256=rbac_sha,

                ),

            ),

        )

    return BootstrapScriptManifest(

        version="test-2.0.0",

        profile="dedicated_schema_v2",

        entries=(

            BootstrapScriptManifestEntry(

                script_code="apply_schema_erp_v010",

                relative_path="01_schema/V010__tablas_bd_erp_completo.sql",

                step_code="apply_schema_erp",

                execution_order=1,

                expected_sha256=erp_sha,

            ),

            BootstrapScriptManifestEntry(

                script_code="apply_schema_tenant_store_v020",

                relative_path="05_dedicated/V020__tenant_identity_rbac_store.sql",

                step_code="apply_schema_rbac",

                execution_order=2,

                expected_sha256=dtsp_sha,

            ),

            BootstrapScriptManifestEntry(

                script_code="apply_schema_rbac_v010",

                relative_path="05_dedicated/V010__rbac_tablas_dedicated.sql",

                step_code="apply_schema_rbac",

                execution_order=3,

                expected_sha256=rbac_sha,

            ),

            BootstrapScriptManifestEntry(

                script_code="apply_schema_auth_audit_v030",

                relative_path="05_dedicated/V030__auth_audit_log_dedicated.sql",

                step_code="apply_schema_rbac",

                execution_order=4,

                expected_sha256=audit_sha,

            ),

        ),

    )





@pytest.fixture

def ddl_client() -> MockBootstrapDdlClient:

    return MockBootstrapDdlClient()





@pytest.mark.unit

def test_f4_05_split_sql_server_batches():

    sql = "SELECT 1;\nGO\nSELECT 2;\nGO\n\nSELECT 3;"

    batches = split_sql_server_batches(sql)

    assert batches == ["SELECT 1;", "SELECT 2;", "SELECT 3;"]





@pytest.mark.unit

def test_f4_05_manifest_order_and_codes_v2_default():

    manifest = load_dedicated_schema_manifest()

    assert manifest.profile == DEDICATED_SCHEMA_MANIFEST_V2.profile

    assert ordered_script_codes(manifest) == (

        "apply_schema_erp_v010",

        "apply_schema_tenant_store_v020",

        "apply_schema_rbac_v010",

        "apply_schema_auth_audit_v030",

    )

    assert manifest.entries[0].step_code == "apply_schema_erp"

    assert manifest.entries[1].step_code == "apply_schema_rbac"

    assert manifest.entries[2].step_code == "apply_schema_rbac"

    assert manifest.entries[3].step_code == "apply_schema_rbac"





@pytest.mark.unit

def test_f4_05_manifest_v1_explicit_profile():

    manifest = load_dedicated_schema_manifest(profile="dedicated_schema_v1")

    assert manifest.profile == DEDICATED_SCHEMA_MANIFEST_V1.profile

    assert ordered_script_codes(manifest) == (

        "apply_schema_erp_v010",

        "apply_schema_rbac_v010",

    )





@pytest.mark.unit

def test_f4_05_validate_manifest_integrity_real_bootstrap_v2():

    manifest = load_dedicated_schema_manifest()

    validate_manifest_integrity(manifest)





@pytest.mark.unit

def test_f4_05_manifest_integrity_fails_on_checksum_drift(tmp_path: Path):

    manifest = _build_temp_manifest_root(tmp_path)

    script_path = tmp_path / manifest.entries[0].relative_path

    script_path.write_text("-- mutated\n", encoding="utf-8")



    with pytest.raises(ValidationError) as exc:

        validate_manifest_integrity(manifest, bootstrap_root=tmp_path)

    assert exc.value.internal_code == "BOOTSTRAP_MANIFEST_INTEGRITY_FAILED"





@pytest.mark.unit

def test_f4_05_discover_manifest_entries(tmp_path: Path):

    manifest = _build_temp_manifest_root(tmp_path)

    discovered = discover_manifest_entries(manifest, bootstrap_root=tmp_path)

    assert len(discovered) == 4

    assert discovered[0][0].script_code == "apply_schema_erp_v010"

    assert discovered[1][0].script_code == "apply_schema_tenant_store_v020"

    assert compute_file_sha256(discovered[0][1]) == manifest.entries[0].expected_sha256





@pytest.mark.unit

@pytest.mark.asyncio

async def test_f4_05_run_executes_scripts_sequentially_v2(

    ddl_client: MockBootstrapDdlClient,

    tmp_path: Path,

):

    manifest = _build_temp_manifest_root(tmp_path)

    runner = BootstrapScriptRunner(

        ddl_client=ddl_client,

        bootstrap_root=tmp_path,

    )



    original_loader = load_dedicated_schema_manifest



    def _load_test_manifest(*, profile: str = "dedicated_schema_v2"):

        if profile != manifest.profile:

            raise ValidationError(

                detail=f"Perfil bootstrap dedicated no soportado: {profile}.",

                internal_code="BOOTSTRAP_PROFILE_UNSUPPORTED",

            )

        return manifest



    import app.infrastructure.provisioning.bootstrap_script_runner as runner_module



    runner_module.load_dedicated_schema_manifest = _load_test_manifest

    try:

        request = BootstrapScriptRunRequest(

            database_name="erp_acme001",

            cliente_id=CLIENTE_ID,

        )

        result = await runner.run_dedicated_schema_bootstrap(request)

    finally:

        runner_module.load_dedicated_schema_manifest = original_loader



    assert result.scripts_executed == (

        "apply_schema_erp_v010",

        "apply_schema_tenant_store_v020",

        "apply_schema_rbac_v010",

        "apply_schema_auth_audit_v030",

    )

    assert result.scripts_skipped == ()

    assert result.batches_executed == 6

    assert ddl_client.tables_created is True

    assert "apply_schema_tenant_store_v020" in ddl_client.markers

    erp_idx = next(

        i for i, (_, sql) in enumerate(ddl_client.executed) if "demo_erp" in sql

    )

    dtsp_idx = next(

        i for i, (_, sql) in enumerate(ddl_client.executed) if "CREATE TABLE modulo" in sql

    )

    rbac_idx = next(

        i

        for i, (_, sql) in enumerate(ddl_client.executed)

        if "rol_permiso" in sql

    )

    assert erp_idx < dtsp_idx < rbac_idx





@pytest.fixture

def patched_runner_module_v2(tmp_path: Path, ddl_client: MockBootstrapDdlClient):

    manifest = _build_temp_manifest_root(tmp_path)

    runner = BootstrapScriptRunner(

        ddl_client=ddl_client,

        bootstrap_root=tmp_path,

    )

    import app.infrastructure.provisioning.bootstrap_script_runner as runner_module



    original_loader = runner_module.load_dedicated_schema_manifest



    def _load_test_manifest(*, profile: str = "dedicated_schema_v2"):

        if profile != manifest.profile:

            raise ValidationError(

                detail=f"Perfil bootstrap dedicated no soportado: {profile}.",

                internal_code="BOOTSTRAP_PROFILE_UNSUPPORTED",

            )

        return manifest



    runner_module.load_dedicated_schema_manifest = _load_test_manifest

    yield runner, manifest

    runner_module.load_dedicated_schema_manifest = original_loader





@pytest.fixture

def patched_runner_module_v1(tmp_path: Path, ddl_client: MockBootstrapDdlClient):

    manifest = _build_temp_manifest_root(tmp_path, profile="dedicated_schema_v1")

    runner = BootstrapScriptRunner(

        ddl_client=ddl_client,

        bootstrap_root=tmp_path,

    )

    import app.infrastructure.provisioning.bootstrap_script_runner as runner_module



    original_loader = runner_module.load_dedicated_schema_manifest



    def _load_test_manifest(*, profile: str = "dedicated_schema_v2"):

        if profile != manifest.profile:

            raise ValidationError(

                detail=f"Perfil bootstrap dedicated no soportado: {profile}.",

                internal_code="BOOTSTRAP_PROFILE_UNSUPPORTED",

            )

        return manifest



    runner_module.load_dedicated_schema_manifest = _load_test_manifest

    yield runner, manifest

    runner_module.load_dedicated_schema_manifest = original_loader





@pytest.mark.unit

@pytest.mark.asyncio

async def test_f4_05_rerun_is_idempotent(

    patched_runner_module_v2,

    ddl_client: MockBootstrapDdlClient,

):

    runner, _manifest = patched_runner_module_v2

    request = BootstrapScriptRunRequest(

        database_name="erp_acme001",

        cliente_id=CLIENTE_ID,

    )



    first = await runner.run_dedicated_schema_bootstrap(request)

    executed_after_first = len(ddl_client.executed)

    second = await runner.run_dedicated_schema_bootstrap(request)



    assert len(first.scripts_executed) == 4

    assert second.scripts_executed == ()

    assert len(second.scripts_skipped) == 4

    new_executions = ddl_client.executed[executed_after_first:]

    assert not any(

        "demo_erp" in sql or "rol_permiso" in sql or "CREATE TABLE modulo" in sql

        for _, sql in new_executions

    )





@pytest.mark.unit

@pytest.mark.asyncio

async def test_f4_05_marker_checksum_mismatch_raises_conflict(

    patched_runner_module_v2,

    ddl_client: MockBootstrapDdlClient,

):

    runner, _manifest = patched_runner_module_v2

    ddl_client.markers["apply_schema_erp_v010"] = "deadbeef" * 8



    request = BootstrapScriptRunRequest(

        database_name="erp_acme001",

        cliente_id=CLIENTE_ID,

    )



    with pytest.raises(ConflictError) as exc:

        await runner.run_dedicated_schema_bootstrap(request)

    assert exc.value.internal_code == "BOOTSTRAP_MARKER_CHECKSUM_MISMATCH"





@pytest.mark.unit

@pytest.mark.asyncio

async def test_f4_05_sql_failure_maps_to_provisioning_schema_failed(

    patched_runner_module_v2,

    ddl_client: MockBootstrapDdlClient,

):

    runner, _manifest = patched_runner_module_v2

    ddl_client.fail_on_script_batch = True



    request = BootstrapScriptRunRequest(

        database_name="erp_acme001",

        cliente_id=CLIENTE_ID,

    )



    with pytest.raises(ConflictError) as exc:

        await runner.run_dedicated_schema_bootstrap(request)

    assert exc.value.internal_code == "PROVISIONING_SCHEMA_FAILED"





@pytest.mark.unit

@pytest.mark.asyncio

async def test_f4_05_v2_missing_runtime_tables_raises_conflict(

    patched_runner_module_v2,

):

    runner, _manifest = patched_runner_module_v2

    ddl_client = MockBootstrapDdlClient(dtsp_tables_exist=False)

    runner._ddl = ddl_client  # noqa: SLF001 — test override



    request = BootstrapScriptRunRequest(

        database_name="erp_acme001",

        cliente_id=CLIENTE_ID,

    )



    with pytest.raises(ConflictError) as exc:

        await runner.run_dedicated_schema_bootstrap(request)

    assert exc.value.internal_code == "PROVISIONING_SCHEMA_FAILED"





@pytest.mark.unit

@pytest.mark.asyncio

async def test_f4_05_v1_skips_dtsp_verification(

    patched_runner_module_v1,

    ddl_client: MockBootstrapDdlClient,

):

    runner, _manifest = patched_runner_module_v1

    ddl_client.dtsp_tables_exist = False

    request = BootstrapScriptRunRequest(

        database_name="erp_acme001",

        cliente_id=CLIENTE_ID,

        profile="dedicated_schema_v1",

    )

    result = await runner.run_dedicated_schema_bootstrap(request)

    assert result.scripts_executed == (

        "apply_schema_erp_v010",

        "apply_schema_rbac_v010",

    )





@pytest.mark.unit

@pytest.mark.asyncio

async def test_f4_05_default_client_disabled_without_injection():

    runner = BootstrapScriptRunner()

    request = BootstrapScriptRunRequest(

        database_name="erp_acme001",

        cliente_id=CLIENTE_ID,

    )

    with pytest.raises(ValidationError) as exc:

        await runner.run_dedicated_schema_bootstrap(request)

    assert exc.value.internal_code == "PROVISIONING_DDL_EXECUTOR_DISABLED"





@pytest.mark.unit

def test_f4_05_unsupported_profile():

    with pytest.raises(ValidationError) as exc:

        load_dedicated_schema_manifest(profile="unknown_profile")

    assert exc.value.internal_code == "BOOTSTRAP_PROFILE_UNSUPPORTED"


