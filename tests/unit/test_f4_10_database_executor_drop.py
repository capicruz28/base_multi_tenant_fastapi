"""PR-F4-10 — tests DROP DedicatedDatabaseExecutor."""
from __future__ import annotations

import re
from uuid import uuid4

import pytest

from app.infrastructure.provisioning.dedicated_database_executor import (
    DedicatedDatabaseExecutor,
)
from app.infrastructure.provisioning.dedicated_database_types import (
    DedicatedDatabaseDropRequest,
)

CLIENTE_ID = uuid4()


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

    def open_session(self, *, database: str = "master") -> _MockDdlSessionContext:
        return _MockDdlSessionContext(self, database)

    async def scalar_int(self, sql: str, *, database: str = "master") -> int | None:
        db_match = re.search(r"DB_ID\(N'((?:''|[^'])*)'\)", sql)
        if db_match:
            name = db_match.group(1).replace("''", "'")
            return 1 if name in self.databases else None
        login_match = re.search(r"SUSER_ID\(N'((?:''|[^'])*)'\)", sql)
        if login_match:
            name = login_match.group(1).replace("''", "'")
            return 1 if name in self.logins else None
        return None

    async def execute(self, sql: str, *, database: str = "master") -> None:
        self.executed.append((database, sql))
        if "DROP DATABASE" in sql:
            bracket = re.search(r"\[([^\]]+)\]", sql)
            if bracket:
                self.databases.discard(bracket.group(1))
        if "DROP LOGIN" in sql:
            bracket = re.search(r"\[([^\]]+)\]", sql)
            if bracket:
                self.logins.discard(bracket.group(1))


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_10_drop_database_and_login():
    client = MockDdlClient()
    client.databases.add("erp_acme001")
    client.logins.add("erpapp_acme001")
    executor = DedicatedDatabaseExecutor(ddl_client=client)

    result = await executor.drop_physical_database(
        DedicatedDatabaseDropRequest(
            cliente_id=CLIENTE_ID,
            database_name="erp_acme001",
            app_login_name="erpapp_acme001",
        ),
    )

    assert result.database_dropped is True
    assert result.login_dropped is True
    assert "erp_acme001" not in client.databases
    assert "erpapp_acme001" not in client.logins
    assert any("DROP DATABASE" in sql for _, sql in client.executed)
    assert any("DROP LOGIN" in sql for _, sql in client.executed)
    assert client.session_opens == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f4_10_drop_idempotent_when_absent():
    client = MockDdlClient()
    executor = DedicatedDatabaseExecutor(ddl_client=client)

    result = await executor.drop_physical_database(
        DedicatedDatabaseDropRequest(
            cliente_id=CLIENTE_ID,
            database_name="erp_acme001",
            app_login_name="erpapp_acme001",
        ),
    )

    assert result.database_dropped is False
    assert result.login_dropped is False
    assert client.executed == []
