"""
Fase 1: permission_sync no desactiva permisos protegidos (core.app.acceder).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.core.authorization.core_permissions import (
    ADMIN_PLATFORM_ACCESS,
    CORE_APP_ACCEDER,
    register_core_permissions,
)
from app.core.authorization.permission_registry import clear, register
from app.core.authorization.permission_sync_service import sync


@pytest.fixture(autouse=True)
def _clean_registry():
    clear()
    yield
    clear()


@pytest.mark.asyncio
async def test_sync_does_not_deactivate_core_app_acceder():
    register_core_permissions()
    register(
        {
            "codigo": "org.empresa.leer",
            "nombre": "Leer empresa",
            "recurso": "empresa",
            "accion": "leer",
            "modulo_codigo": "ORG",
        }
    )

    existing_rows = [
        {"permiso_id": "p-core", "codigo": CORE_APP_ACCEDER},
        {"permiso_id": "p-org", "codigo": "org.empresa.leer"},
        {"permiso_id": "p-legacy", "codigo": "legacy.only.in.db"},
    ]

    disabled: list[str] = []

    async def fake_execute_update(sql, **kwargs):
        sql_text = str(sql)
        if "es_activo = 0" not in sql_text:
            return
        codigo = getattr(sql, "_bindparams", {}).get("codigo")
        if codigo is not None:
            val = codigo.value if hasattr(codigo, "value") else codigo
            disabled.append(str(val))

    with (
        patch(
            "app.core.authorization.permission_sync_service.execute_query",
            new=AsyncMock(return_value=existing_rows),
        ),
        patch(
            "app.core.authorization.permission_sync_service.execute_insert",
            new=AsyncMock(),
        ),
        patch(
            "app.core.authorization.permission_sync_service.execute_update",
            new=fake_execute_update,
        ),
        patch(
            "app.core.authorization.permission_sync_service._get_modulo_id_by_codigo",
            new=AsyncMock(return_value=None),
        ),
    ):
        await sync()

    assert CORE_APP_ACCEDER not in disabled
    assert ADMIN_PLATFORM_ACCESS not in disabled
    assert "legacy.only.in.db" in disabled
    assert "org.empresa.leer" not in disabled


@pytest.mark.asyncio
async def test_register_core_permissions_idempotent():
    register_core_permissions()
    register_core_permissions()
    from app.core.authorization.permission_registry import get_by_codigo

    meta = get_by_codigo(CORE_APP_ACCEDER)
    assert meta is not None
    assert meta["codigo"] == CORE_APP_ACCEDER
    assert meta["recurso"] == "app"
    assert meta["accion"] == "acceder"
