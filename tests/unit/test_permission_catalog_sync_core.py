"""F12-B — tests unitarios permission_catalog_sync_core."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.core.authorization.core_permissions import (
    ADMIN_PLATFORM_ACCESS,
    ADMIN_TENANT_ACCESS,
    CORE_APP_ACCEDER,
)
from app.core.authorization.permission_catalog_sync_core import (
    compute_registry_hash,
    should_deactivate_permiso,
    sync_permission_catalog,
)
from app.core.authorization.permission_catalog_sync_types import SyncMode


class MockCatalogExecutor:
    def __init__(self, existing: list[dict] | None = None) -> None:
        self.existing = list(existing or [])
        self.inserted: list[str] = []
        self.updated: list[str] = []
        self.deactivated: list[str] = []
        self.modulo_map: dict[str, str | None] = {}

    async def fetch_existing(self) -> list[dict]:
        return list(self.existing)

    async def resolve_modulo_id(self, modulo_codigo: str) -> str | None:
        return self.modulo_map.get(modulo_codigo)

    async def insert_permiso(self, *, codigo: str, **kwargs) -> None:
        self.inserted.append(codigo)
        self.existing.append({"permiso_id": kwargs["permiso_id"], "codigo": codigo})

    async def update_permiso(self, *, codigo: str, **kwargs) -> None:
        self.updated.append(codigo)

    async def deactivate_permiso(self, codigo: str) -> None:
        self.deactivated.append(codigo)


@pytest.mark.unit
def test_compute_registry_hash_is_stable():
    declared = [
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
    first = compute_registry_hash(declared)
    second = compute_registry_hash(list(reversed(declared)))
    assert first == second
    assert len(first) == 64


@pytest.mark.unit
@pytest.mark.parametrize(
    ("codigo", "mode", "declared", "expected"),
    [
        ("admin.usuario.leer", SyncMode.DEDICATED_DATA_PLANE, {"admin.usuario.leer"}, False),
        ("org.empresa.leer", SyncMode.DEDICATED_DATA_PLANE, {"admin.usuario.leer"}, False),
        ("admin.legacy.only", SyncMode.DEDICATED_DATA_PLANE, {"admin.usuario.leer"}, True),
        ("legacy.only", SyncMode.CONTROL_PLANE, {"admin.usuario.leer"}, True),
        (CORE_APP_ACCEDER, SyncMode.CONTROL_PLANE, set(), False),
        (ADMIN_PLATFORM_ACCESS, SyncMode.DEDICATED_DATA_PLANE, set(), False),
        (ADMIN_TENANT_ACCESS, SyncMode.DEDICATED_DATA_PLANE, set(), False),
    ],
)
def test_should_deactivate_permiso_rules(codigo, mode, declared, expected):
    assert should_deactivate_permiso(codigo, declared, mode) is expected


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sync_control_plane_deactivates_unknown_permissions():
    executor = MockCatalogExecutor(
        existing=[
            {"permiso_id": "1", "codigo": CORE_APP_ACCEDER},
            {"permiso_id": "2", "codigo": "legacy.only.in.db"},
        ]
    )
    declared = [
        {
            "codigo": CORE_APP_ACCEDER,
            "nombre": "Acceder",
            "recurso": "app",
            "accion": "acceder",
            "modulo_codigo": None,
        }
    ]
    result = await sync_permission_catalog(
        declared=declared,
        executor=executor,
        mode=SyncMode.CONTROL_PLANE,
    )
    assert result.updated == 1
    assert CORE_APP_ACCEDER not in executor.deactivated
    assert "legacy.only.in.db" in executor.deactivated


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sync_dedicated_does_not_deactivate_org_permissions():
    executor = MockCatalogExecutor(
        existing=[
            {"permiso_id": "1", "codigo": "org.empresa.leer"},
            {"permiso_id": "2", "codigo": "admin.legacy.only"},
            {"permiso_id": "3", "codigo": ADMIN_TENANT_ACCESS},
        ]
    )
    declared = [
        {
            "codigo": "admin.usuario.leer",
            "nombre": "Leer usuarios",
            "recurso": "usuario",
            "accion": "leer",
            "modulo_codigo": "ADMIN",
        }
    ]
    executor.modulo_map["ADMIN"] = "mod-admin-id"

    result = await sync_permission_catalog(
        declared=declared,
        executor=executor,
        mode=SyncMode.DEDICATED_DATA_PLANE,
    )

    assert "admin.usuario.leer" in executor.inserted
    assert "org.empresa.leer" not in executor.deactivated
    assert ADMIN_TENANT_ACCESS not in executor.deactivated
    assert "admin.legacy.only" in executor.deactivated
    assert result.deactivated == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sync_inserts_missing_declared_permissions():
    executor = MockCatalogExecutor()
    declared = [
        {
            "codigo": "admin.rol.leer",
            "nombre": "Leer roles",
            "recurso": "rol",
            "accion": "leer",
            "modulo_codigo": None,
        }
    ]
    result = await sync_permission_catalog(
        declared=declared,
        executor=executor,
        mode=SyncMode.DEDICATED_DATA_PLANE,
    )
    assert result.inserted == 1
    assert executor.inserted == ["admin.rol.leer"]
