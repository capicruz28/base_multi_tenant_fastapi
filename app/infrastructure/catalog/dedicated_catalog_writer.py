"""Escritura y lectura dedicated Product Reference — F14."""
from __future__ import annotations

import logging
from contextlib import AbstractAsyncContextManager
from typing import Any, Callable, Optional, Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.catalog.catalog_sync_definitions import (
    CatalogDefinition,
    CatalogKind,
    get_catalog_definition,
)
from app.core.catalog.catalog_sync_core import summarize_sync_plan
from app.core.catalog.catalog_sync_types import (
    CatalogSyncCounts,
    SyncAction,
    SyncPlan,
    SyncPlanEntry,
)
from app.core.exceptions import ConflictError, DatabaseError
from app.infrastructure.provisioning.dedicated_database_naming import assert_sql_identifier
from app.infrastructure.provisioning.provisioning_dedicated_session import (
    provisioning_dedicated_session,
)

logger = logging.getLogger(__name__)

DedicatedSessionFactory = Callable[[str], AbstractAsyncContextManager[AsyncSession]]


def _sql_value(column: str, value: Any) -> Any:
    if value is None:
        if column == "decimales":
            return 2
        if column == "es_activo":
            return 1
        return None
    if column == "es_activo":
        return 1 if bool(value) else 0
    if column.endswith("_id"):
        return str(value)
    return value


class DedicatedCatalogWriter:
    """Writer genérico sobre cat_* en BD dedicated."""

    def __init__(
        self,
        session_factory: Optional[DedicatedSessionFactory] = None,
    ) -> None:
        self._session_factory = session_factory or provisioning_dedicated_session

    async def ping(self, database_name: str) -> None:
        assert_sql_identifier(database_name, field="database_name")
        try:
            async with self._session_factory(database_name) as session:
                await session.execute(text("SELECT 1"))
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError(
                detail="BD dedicada no alcanzable.",
                internal_code="DEDICATED_UNREACHABLE",
            ) from exc

    async def fetch_all(
        self,
        kind: CatalogKind,
        database_name: str,
    ) -> list[dict[str, Any]]:
        assert_sql_identifier(database_name, field="database_name")
        definition = get_catalog_definition(kind)
        columns = [definition.primary_key, *definition.compare_columns]
        sql_columns = ", ".join(f"[{col}]" for col in columns)
        sql = f"SELECT {sql_columns} FROM [{definition.table_name}]"
        try:
            async with self._session_factory(database_name) as session:
                result = await session.execute(text(sql))
                keys = list(result.keys())
                return [dict(zip(keys, row)) for row in result.fetchall()]
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError(
                detail="Error leyendo catálogo en BD dedicada.",
                internal_code="DEDICATED_CATALOG_READ_FAILED",
            ) from exc

    async def existing_primary_keys(
        self,
        kind: CatalogKind,
        database_name: str,
        primary_keys: Sequence[str],
    ) -> set[str]:
        if not primary_keys:
            return set()
        assert_sql_identifier(database_name, field="database_name")
        definition = get_catalog_definition(kind)
        normalized = sorted({pk.strip().lower() for pk in primary_keys if pk})
        if not normalized:
            return set()

        placeholders = ", ".join(f":pk_{index}" for index in range(len(normalized)))
        params = {f"pk_{index}": pk for index, pk in enumerate(normalized)}
        sql = (
            f"SELECT [{definition.primary_key}] AS pk "
            f"FROM [{definition.table_name}] "
            f"WHERE [{definition.primary_key}] IN ({placeholders})"
        )
        try:
            async with self._session_factory(database_name) as session:
                result = await session.execute(text(sql), params)
                return {str(row[0]).strip().lower() for row in result.fetchall()}
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError(
                detail="Error verificando claves en BD dedicada.",
                internal_code="DEDICATED_CATALOG_READ_FAILED",
            ) from exc

    async def apply_plan(
        self,
        kind: CatalogKind,
        database_name: str,
        plan: SyncPlan,
        *,
        platform_total: int,
        dedicated_before: int,
    ) -> CatalogSyncCounts:
        assert_sql_identifier(database_name, field="database_name")
        definition = get_catalog_definition(kind)
        summary = summarize_sync_plan(plan)
        try:
            async with self._session_factory(database_name) as session:
                for entry in plan.entries:
                    await self._apply_entry(session, definition, entry)
        except DatabaseError:
            raise
        except Exception as exc:
            raise ConflictError(
                detail="Error aplicando sincronización de catálogo en BD dedicada.",
                internal_code="CATALOG_SYNC_APPLY_FAILED",
            ) from exc

        return CatalogSyncCounts(
            inserted=summary["inserted"],
            updated=summary["updated"],
            skipped=summary["skipped"],
            deactivated=summary["deactivated"],
            platform_total=platform_total,
            dedicated_before=dedicated_before,
        )

    async def _apply_entry(
        self,
        session: AsyncSession,
        definition: CatalogDefinition,
        entry: SyncPlanEntry,
    ) -> None:
        if entry.action == SyncAction.SKIP:
            return

        pk_column = definition.primary_key
        table_name = definition.table_name
        pk_value = entry.primary_key

        if entry.action == SyncAction.SOFT_DEACTIVATE:
            sql = (
                f"UPDATE [{table_name}] "
                f"SET [es_activo] = 0 "
                f"WHERE [{pk_column}] = :pk"
            )
            await session.execute(text(sql), {"pk": pk_value})
            return

        if entry.payload is None:
            raise ConflictError(
                detail="Entrada de plan sin payload para mutación.",
                internal_code="CATALOG_SYNC_PLAN_INVALID",
            )

        if entry.action == SyncAction.INSERT:
            columns = [pk_column, *definition.compare_columns]
            col_sql = ", ".join(f"[{col}]" for col in columns)
            val_sql = ", ".join(f":{col}" for col in columns)
            params = {pk_column: pk_value}
            for column in definition.compare_columns:
                params[column] = _sql_value(column, entry.payload.get(column))
            sql = f"INSERT INTO [{table_name}] ({col_sql}) VALUES ({val_sql})"
            await session.execute(text(sql), params)
            return

        if entry.action == SyncAction.UPDATE:
            set_parts = [f"[{col}] = :{col}" for col in definition.compare_columns]
            params = {pk_column: pk_value}
            for column in definition.compare_columns:
                params[column] = _sql_value(column, entry.payload.get(column))
            sql = (
                f"UPDATE [{table_name}] "
                f"SET {', '.join(set_parts)} "
                f"WHERE [{pk_column}] = :{pk_column}"
            )
            await session.execute(text(sql), params)
            return

        raise ConflictError(
            detail=f"Acción de sync no soportada: {entry.action}.",
            internal_code="CATALOG_SYNC_PLAN_INVALID",
        )


__all__ = ["DedicatedCatalogWriter", "DedicatedSessionFactory"]
