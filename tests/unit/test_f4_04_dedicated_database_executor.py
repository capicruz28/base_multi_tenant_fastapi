"""PR-F4-04 — tests unitarios DedicatedDatabaseExecutor."""
from __future__ import annotations

import re
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, DatabaseError, ValidationError
from app.infrastructure.provisioning.dedicated_database_executor import (
    DedicatedDatabaseExecutor,
)
from app.infrastructure.provisioning.dedicated_database_naming import (
    build_dedicated_app_login_name,
    build_dedicated_database_name,
)
from app.infrastructure.provisioning.dedicated_database_types import (
    DedicatedDatabaseProvisionRequest,
)
from app.infrastructure.provisioning.dedicated_ddl_client import (
    validate_provisioning_ddl_settings,
)

CLIENTE_ID = uuid4()

_DB_ID_RE = re.compile(r"DB_ID\(N'((?:''|[^'])*)'\)")
_SUSER_ID_RE = re.compile(r"SUSER_ID\(N'((?:''|[^'])*)'\)")


class MockDdlSession:
    def __init__(self, client: "MockDdlClient", database: str) -> None:
        self._client = client
        self._database = database

    async def scalar_int(self, sql: str) -> int | None:
        return await self._client.scalar_int(sql, database=self._database)

    async def execute(self, sql: str) -> None:
        await self._client.execute(sql, database=self._database)


class _MockDdlSessionContext:
    def __init__(self, client: "MockDdlClient", database: str) -> None:
        self._client = client
        self._database = database

    async def __aenter__(self) -> MockDdlSession:
        self._client.session_opens += 1
        return MockDdlSession(self._client, self._database)

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


class MockDdlClient:
    def __init__(self) -> None:
        self.databases: set[str] = set()
        self.logins: set[str] = set()
        self.executed: list[tuple[str, str]] = []
        self.session_opens: int = 0
        self.fail_on_create_db = False
        self.fail_on_create_db_duplicate = False

    def open_session(self, *, database: str = "master") -> _MockDdlSessionContext:
        return _MockDdlSessionContext(self, database)

    async def scalar_int(self, sql: str, *, database: str = "master") -> int | None:
        db_match = _DB_ID_RE.search(sql)
        if db_match:
            name = db_match.group(1).replace("''", "'")
            return 1 if name in self.databases else None
        login_match = _SUSER_ID_RE.search(sql)
        if login_match:
            name = login_match.group(1).replace("''", "'")
            return 1 if name in self.logins else None
        return None

    async def execute(self, sql: str, *, database: str = "master") -> None:
        self.executed.append((database, sql))
        if "CREATE DATABASE" in sql and self.fail_on_create_db_duplicate:
            raise DatabaseError(
                detail="Error ejecutando sentencia DDL de plataforma.",
                internal_code="DDL_EXECUTE_FAILED",
            ) from RuntimeError("Database 'erp_acme001' already exists. Error 1801")
        if "CREATE DATABASE" in sql and self.fail_on_create_db:
            raise DatabaseError(
                detail="Error ejecutando sentencia DDL de plataforma.",
                internal_code="DDL_EXECUTE_FAILED",
            ) from RuntimeError("permission denied")
        if "CREATE DATABASE" in sql:
            bracket = re.search(r"\[([^\]]+)\]", sql)
            if bracket:
                self.databases.add(bracket.group(1))
        if "CREATE LOGIN" in sql:
            bracket = re.search(r"\[([^\]]+)\]", sql)
            if bracket:
                self.logins.add(bracket.group(1))


@pytest.fixture
def ddl_client() -> MockDdlClient:
    return MockDdlClient()


@pytest.fixture
def executor(ddl_client: MockDdlClient) -> DedicatedDatabaseExecutor:
    return DedicatedDatabaseExecutor(ddl_client=ddl_client)


@pytest.mark.unit
def test_f4_04_naming_policy_builds_database_and_login():
    db_name = build_dedicated_database_name("ACME-001", cliente_id=CLIENTE_ID)
    login_name = build_dedicated_app_login_name("ACME-001", cliente_id=CLIENTE_ID)
    assert db_name == "erp_acme_001"
    assert login_name == "erpapp_acme_001"


@pytest.mark.unit
def test_f4_04_naming_rejects_empty_codigo():
    with pytest.raises(ValidationError) as exc:
        build_dedicated_database_name("   ", cliente_id=CLIENTE_ID)
    assert exc.value.internal_code == "INVALID_DEDICATED_CODIGO"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_04_provision_creates_database_and_login(
    executor: DedicatedDatabaseExecutor,
    ddl_client: MockDdlClient,
):
    request = DedicatedDatabaseProvisionRequest(
        cliente_id=CLIENTE_ID,
        codigo_cliente="ACME001",
        servidor="sql-staging.local",
        app_login_password="Str0ngP@ssw0rd!",
    )

    result = await executor.provision_physical_database(request)

    assert result.database_name == "erp_acme001"
    assert result.app_login_name == "erpapp_acme001"
    assert result.servidor == "sql-staging.local"
    assert result.app_login_password == "Str0ngP@ssw0rd!"
    assert result.database_created is True
    assert result.login_created is True
    assert result.database_already_existed is False
    assert result.login_already_existed is False
    assert any("CREATE DATABASE" in sql for _, sql in ddl_client.executed)
    assert any("CREATE LOGIN" in sql for _, sql in ddl_client.executed)
    assert any("db_owner" in sql for _, sql in ddl_client.executed)
    assert ddl_client.session_opens == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_04_provision_idempotent_when_database_and_login_exist(
    executor: DedicatedDatabaseExecutor,
    ddl_client: MockDdlClient,
):
    ddl_client.databases.add("erp_acme001")
    ddl_client.logins.add("erpapp_acme001")

    request = DedicatedDatabaseProvisionRequest(
        cliente_id=CLIENTE_ID,
        codigo_cliente="ACME001",
        servidor="sql-staging.local",
    )

    result = await executor.provision_physical_database(request)

    assert result.database_created is False
    assert result.login_created is False
    assert result.database_already_existed is True
    assert result.login_already_existed is True
    assert not any("CREATE DATABASE" in sql for _, sql in ddl_client.executed)
    assert not any("CREATE LOGIN" in sql for _, sql in ddl_client.executed)
    assert any("db_owner" in sql for _, sql in ddl_client.executed)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_04_provision_maps_ddl_failure_to_conflict(
    executor: DedicatedDatabaseExecutor,
    ddl_client: MockDdlClient,
):
    ddl_client.fail_on_create_db = True

    request = DedicatedDatabaseProvisionRequest(
        cliente_id=CLIENTE_ID,
        codigo_cliente="ACME001",
        servidor="sql-staging.local",
    )

    with pytest.raises(ConflictError) as exc:
        await executor.provision_physical_database(request)
    assert exc.value.internal_code == "DEDICATED_DB_CREATE_FAILED"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_04_create_database_treats_duplicate_as_idempotent(
    executor: DedicatedDatabaseExecutor,
    ddl_client: MockDdlClient,
):
    ddl_client.fail_on_create_db_duplicate = True

    request = DedicatedDatabaseProvisionRequest(
        cliente_id=CLIENTE_ID,
        codigo_cliente="ACME001",
        servidor="sql-staging.local",
    )

    result = await executor.provision_physical_database(request)

    assert result.database_created is True
    assert any("CREATE DATABASE" in sql for _, sql in ddl_client.executed)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_04_default_client_disabled_without_injection():
    executor = DedicatedDatabaseExecutor()
    with pytest.raises(ValidationError) as exc:
        await executor.database_exists("erp_test")
    assert exc.value.internal_code == "PROVISIONING_DDL_EXECUTOR_DISABLED"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_04_missing_server_raises_validation(
    executor: DedicatedDatabaseExecutor,
):
    request = DedicatedDatabaseProvisionRequest(
        cliente_id=CLIENTE_ID,
        codigo_cliente="ACME001",
    )
    with pytest.raises(ValidationError) as exc:
        await executor.provision_physical_database(request)
    assert exc.value.internal_code == "PROVISIONING_DDL_SERVER_MISSING"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_04_database_exists_uses_scalar_int(
    executor: DedicatedDatabaseExecutor,
    ddl_client: MockDdlClient,
):
    ddl_client.databases.add("erp_demo")
    assert await executor.database_exists("erp_demo") is True
    assert await executor.database_exists("erp_other") is False


@pytest.mark.unit
def test_f4_04_validate_ddl_settings_incomplete(monkeypatch):
    monkeypatch.setenv("PROVISIONING_DDL_SERVER", "")
    monkeypatch.setenv("PROVISIONING_DDL_USER", "")
    monkeypatch.setenv("PROVISIONING_DDL_PASSWORD", "")

    from app.core.config import Settings

    test_settings = Settings()
    monkeypatch.setattr(
        "app.infrastructure.provisioning.dedicated_ddl_client.settings",
        test_settings,
    )

    with pytest.raises(ValidationError) as exc:
        validate_provisioning_ddl_settings()
    assert exc.value.internal_code == "PROVISIONING_DDL_CONFIG_INCOMPLETE"
