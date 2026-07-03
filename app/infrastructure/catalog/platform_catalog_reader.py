"""Lectura SSOT Product Reference desde BD ERP shared — F14."""
from __future__ import annotations

import logging
import os
from typing import Any, Optional, Sequence
from uuid import UUID

from sqlalchemy import Table, select
from sqlalchemy.sql import text

from app.core.catalog.catalog_sync_definitions import (
    CatalogDefinition,
    CatalogKind,
    canonical_primary_key,
    get_catalog_definition,
)
from app.core.config import settings
from app.core.exceptions import DatabaseError, ValidationError
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_query
from app.infrastructure.database.tables_erp import (
    CatDepartamentoTable,
    CatDistritoTable,
    CatMonedaTable,
    CatPaisTable,
    CatProvinciaTable,
)

logger = logging.getLogger(__name__)

_CATALOG_TABLES: dict[CatalogKind, Table] = {
    CatalogKind.MONEDA: CatMonedaTable,
    CatalogKind.PAIS: CatPaisTable,
    CatalogKind.DEPARTAMENTO: CatDepartamentoTable,
    CatalogKind.PROVINCIA: CatProvinciaTable,
    CatalogKind.DISTRITO: CatDistritoTable,
}

_platform_reference_cliente_id_cache: Optional[UUID] = None


class PlatformCatalogReader:
    """Lector genérico de catálogos Product Reference en BD ERP shared."""

    def __init__(self, *, platform_cliente_id: Optional[UUID] = None) -> None:
        self._platform_cliente_id = platform_cliente_id

    async def resolve_platform_cliente_id(self) -> UUID:
        if self._platform_cliente_id is not None:
            return self._platform_cliente_id
        global _platform_reference_cliente_id_cache
        if _platform_reference_cliente_id_cache is not None:
            return _platform_reference_cliente_id_cache

        env_value = (os.getenv("PLATFORM_CATALOG_REFERENCE_CLIENTE_ID") or "").strip()
        if env_value:
            try:
                resolved = UUID(env_value)
            except ValueError as exc:
                raise ValidationError(
                    detail="PLATFORM_CATALOG_REFERENCE_CLIENTE_ID inválido.",
                    internal_code="PLATFORM_CATALOG_REFERENCE_CLIENT_INVALID",
                ) from exc
            _platform_reference_cliente_id_cache = resolved
            return resolved

        codigo = (settings.SUPERADMIN_CLIENTE_CODIGO or "SYSTEM").strip()
        rows = await execute_query(
            text(
                "SELECT cliente_id FROM cliente "
                "WHERE codigo_cliente = :codigo AND es_activo = 1"
            ).bindparams(codigo=codigo),
            connection_type=DatabaseConnection.ADMIN,
            client_id=None,
        )
        if not rows:
            raise ValidationError(
                detail=(
                    f"No se encontró tenant Platform de referencia (codigo_cliente={codigo}). "
                    "Configure PLATFORM_CATALOG_REFERENCE_CLIENTE_ID."
                ),
                internal_code="PLATFORM_CATALOG_REFERENCE_NOT_FOUND",
            )
        resolved = rows[0]["cliente_id"]
        if isinstance(resolved, UUID):
            _platform_reference_cliente_id_cache = resolved
            return resolved
        _platform_reference_cliente_id_cache = UUID(str(resolved))
        return _platform_reference_cliente_id_cache

    def get_table(self, kind: CatalogKind) -> Table:
        try:
            return _CATALOG_TABLES[kind]
        except KeyError as exc:
            raise ValidationError(
                detail=f"Catálogo no soportado: {kind.value}.",
                internal_code="CATALOG_KIND_NOT_SUPPORTED",
            ) from exc

    async def fetch_all(self, kind: CatalogKind) -> list[dict[str, Any]]:
        definition = get_catalog_definition(kind)
        client_id = await self.resolve_platform_cliente_id()
        table = self.get_table(kind)
        query = select(table)
        try:
            rows = await execute_query(query, client_id=client_id)
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError(
                detail="Error leyendo catálogo Product Reference en Platform.",
                internal_code="PLATFORM_CATALOG_READ_FAILED",
            ) from exc
        logger.debug(
            "Platform catalog read kind=%s client_id=%s rows=%s",
            kind.value,
            client_id,
            len(rows),
        )
        return rows

    async def fetch_distinct_parent_fk_values(
        self,
        kind: CatalogKind,
    ) -> set[str]:
        definition = get_catalog_definition(kind)
        if not definition.parent_fk_column:
            return set()
        rows = await self.fetch_all(kind)
        values: set[str] = set()
        for row in rows:
            raw = row.get(definition.parent_fk_column)
            if raw is None:
                continue
            values.add(str(raw).strip().lower())
        return values


def collect_primary_keys(
    rows: Sequence[dict[str, Any]],
    definition: CatalogDefinition,
) -> set[str]:
    keys: set[str] = set()
    for row in rows:
        pk = canonical_primary_key(row, definition)
        if pk:
            keys.add(pk)
    return keys


__all__ = [
    "PlatformCatalogReader",
    "collect_primary_keys",
]
