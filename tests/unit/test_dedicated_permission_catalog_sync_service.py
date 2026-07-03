"""F12-B — tests unitarios DedicatedPermissionCatalogSyncService."""
from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization.permission_catalog_sync_core import compute_registry_hash
from app.infrastructure.provisioning.dedicated_permission_catalog_sync_service import (
    SCRIPT_CODE,
    DedicatedPermissionCatalogSyncService,
)
from app.infrastructure.provisioning.dedicated_permission_catalog_sync_types import (
    DedicatedPermissionCatalogSyncRequest,
)

CLIENTE_ID = uuid4()


class MockResult:
    def __init__(self, *, fetchone_value=None) -> None:
        self._fetchone_value = fetchone_value

    def fetchone(self):
        return self._fetchone_value


class MockSyncSession:
    def __init__(self, *, marker_hash: str | None = None) -> None:
        self.marker_hash = marker_hash
        self.executed: list[str] = []
        self.marker_upserts: list[str] = []

    async def execute(self, statement, params=None):
        sql = str(statement)
        self.executed.append(sql)
        if "FROM bootstrap_applied" in sql and SCRIPT_CODE in sql:
            if self.marker_hash is None:
                return MockResult(fetchone_value=None)
            return MockResult(fetchone_value=(self.marker_hash,))
        if "SELECT 1 FROM bootstrap_applied" in sql:
            return MockResult(fetchone_value=(1,) if self.marker_hash else None)
        return MockResult()


def _declared_sample():
    return [
        {
            "codigo": "admin.usuario.leer",
            "nombre": "Leer usuarios",
            "recurso": "usuario",
            "accion": "leer",
            "modulo_codigo": "ADMIN",
        },
        {
            "codigo": "core.app.acceder",
            "nombre": "Acceder",
            "recurso": "app",
            "accion": "acceder",
            "modulo_codigo": None,
        },
    ]


def _session_factory(session: MockSyncSession):
    @asynccontextmanager
    async def _factory(_database_name: str):
        yield session

    return _factory


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_sync_disabled_by_config():
    session = MockSyncSession()
    service = DedicatedPermissionCatalogSyncService(
        session_factory=_session_factory(session),
    )
    request = DedicatedPermissionCatalogSyncRequest(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
    )
    with patch(
        "app.infrastructure.provisioning.dedicated_permission_catalog_sync_service.settings.DEDICATED_PERMISSION_CATALOG_SYNC_ENABLED",
        False,
    ):
        result = await service.run_sync(request, declared=_declared_sample())

    assert result.status == "disabled"
    assert not session.executed


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_sync_skips_when_marker_matches_registry_hash():
    declared = _declared_sample()
    registry_hash = compute_registry_hash(declared)
    session = MockSyncSession(marker_hash=registry_hash)
    service = DedicatedPermissionCatalogSyncService(
        session_factory=_session_factory(session),
    )
    request = DedicatedPermissionCatalogSyncRequest(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
    )

    with patch(
        "app.infrastructure.provisioning.dedicated_permission_catalog_sync_service.sync_permission_catalog",
        new=AsyncMock(),
    ) as sync_mock:
        result = await service.run_sync(request, declared=declared)

    sync_mock.assert_not_called()
    assert result.status == "skipped"
    assert result.registry_hash == registry_hash


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_sync_applies_and_records_marker():
    declared = _declared_sample()
    registry_hash = compute_registry_hash(declared)
    session = MockSyncSession(marker_hash=None)
    service = DedicatedPermissionCatalogSyncService(
        session_factory=_session_factory(session),
    )
    request = DedicatedPermissionCatalogSyncRequest(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
    )

    with patch(
        "app.infrastructure.provisioning.dedicated_permission_catalog_sync_service.sync_permission_catalog",
        new=AsyncMock(
            return_value=type(
                "R",
                (),
                {
                    "inserted": 2,
                    "updated": 0,
                    "deactivated": 1,
                    "declared_count": 2,
                },
            )()
        ),
    ):
        result = await service.run_sync(request, declared=declared)

    assert result.status == "applied"
    assert result.registry_hash == registry_hash
    assert result.inserted == 2
    assert result.deactivated == 1
    assert any("INSERT INTO bootstrap_applied" in sql for sql in session.executed)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_sync_updates_marker_when_registry_hash_changes():
    declared = _declared_sample()
    new_hash = compute_registry_hash(declared)
    session = MockSyncSession(marker_hash="old-hash")
    service = DedicatedPermissionCatalogSyncService(
        session_factory=_session_factory(session),
    )
    request = DedicatedPermissionCatalogSyncRequest(
        database_name="erp_acme001",
        cliente_id=CLIENTE_ID,
    )

    with patch(
        "app.infrastructure.provisioning.dedicated_permission_catalog_sync_service.sync_permission_catalog",
        new=AsyncMock(
            return_value=type(
                "R",
                (),
                {
                    "inserted": 1,
                    "updated": 1,
                    "deactivated": 0,
                    "declared_count": 2,
                },
            )()
        ),
    ):
        result = await service.run_sync(request, declared=declared)

    assert result.status == "applied"
    assert result.registry_hash == new_hash
    assert any("UPDATE bootstrap_applied" in sql for sql in session.executed)
