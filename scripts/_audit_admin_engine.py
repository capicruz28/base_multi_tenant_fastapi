#!/usr/bin/env python3
"""Auditoría runtime: engine ADMIN usado por execute_update(ADMIN)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.infrastructure.database.connection_async import (
    DatabaseConnection,
    _async_engines,
    _build_async_connection_string,
    _get_async_engine,
    get_db_connection,
)


async def main() -> None:
    print("=== settings (runtime) ===")
    print(f"DB_DATABASE={settings.DB_DATABASE!r}")
    print(f"DB_ADMIN_DATABASE={settings.DB_ADMIN_DATABASE!r}")
    print(f"DB_ADMIN_SERVER={settings.DB_ADMIN_SERVER!r}")
    print(f"DB_ADMIN_PORT={settings.DB_ADMIN_PORT!r}")

    conn_str = _build_async_connection_string(DatabaseConnection.ADMIN)
    print("\n=== _build_async_connection_string(ADMIN) ===")
    # mask password in URL for display
    safe = conn_str
    if settings.DB_ADMIN_PASSWORD:
        safe = safe.replace(settings.DB_ADMIN_PASSWORD, "***")
    print(safe)

    print(f"\n=== _async_engines before first use: keys={list(_async_engines.keys())} id={id(_async_engines)} ===")

    engine = _get_async_engine(DatabaseConnection.ADMIN)
    print("\n=== after _get_async_engine(ADMIN) ===")
    print(f"engine_key present: {'admin' in _async_engines}")
    print(f"_async_engines id={id(_async_engines)}")
    print(f"engine object id={id(engine)}")
    print(f"engine.url (full) = {engine.url}")

    engine2 = _get_async_engine(DatabaseConnection.ADMIN)
    print(f"\nsecond _get_async_engine(ADMIN) same object? {engine2 is engine}")

    # Ruta exacta actualizar_cliente: execute_update -> _get_connection_context(ADMIN) -> get_db_connection(ADMIN)
    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        engine_via_ctx = session.get_bind()
        print("\n=== via get_db_connection(ADMIN) session.get_bind() ===")
        print(f"bind is cached engine? {engine_via_ctx is engine}")
        print(f"bind.url = {engine_via_ctx.url}")

        result = await session.execute(
            __import__("sqlalchemy").text("SELECT DB_NAME() AS current_db")
        )
        row = result.first()
        print(f"SELECT DB_NAME() = {row[0] if row else None}")

    print(f"\n=== _async_engines keys after use: {list(_async_engines.keys())} ===")


if __name__ == "__main__":
    asyncio.run(main())
