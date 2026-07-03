"""Motor de sincronización Product Reference — un catálogo, un tenant (F14)."""
from __future__ import annotations

import logging
import time
from typing import Optional
from uuid import UUID

from app.core.catalog.catalog_sync_core import compute_sync_plan
from app.core.catalog.catalog_sync_definitions import CatalogKind, get_catalog_definition
from app.core.catalog.catalog_sync_types import (
    CatalogSyncCounts,
    CatalogSyncErrorDetail,
    CatalogSyncResult,
    CatalogSyncStatus,
)
from app.core.exceptions import CustomException
from app.infrastructure.catalog.dedicated_catalog_writer import DedicatedCatalogWriter
from app.infrastructure.catalog.platform_catalog_reader import PlatformCatalogReader

logger = logging.getLogger(__name__)


class CatalogSyncService:
    """Orquesta Reader → Core → Writer para un (cliente_id, catálogo)."""

    def __init__(
        self,
        *,
        reader: Optional[PlatformCatalogReader] = None,
        writer: Optional[DedicatedCatalogWriter] = None,
    ) -> None:
        self._reader = reader or PlatformCatalogReader()
        self._writer = writer or DedicatedCatalogWriter()

    async def run(
        self,
        *,
        cliente_id: UUID,
        catalog: CatalogKind,
        database_name: str,
    ) -> CatalogSyncResult:
        definition = get_catalog_definition(catalog)
        started = time.perf_counter()
        try:
            platform_rows = await self._reader.fetch_all(catalog)
            dedicated_rows = await self._writer.fetch_all(catalog, database_name)
            dedicated_before = len(dedicated_rows)

            plan = compute_sync_plan(
                platform_rows=platform_rows,
                dedicated_rows=dedicated_rows,
                definition=definition,
            )
            counts = await self._writer.apply_plan(
                catalog,
                database_name,
                plan,
                platform_total=len(platform_rows),
                dedicated_before=dedicated_before,
            )
            duration_ms = int((time.perf_counter() - started) * 1000)
            logger.info(
                "Catalog sync completed catalog=%s cliente_id=%s database=%s "
                "inserted=%s updated=%s skipped=%s deactivated=%s duration_ms=%s",
                catalog.value,
                cliente_id,
                database_name,
                counts.inserted,
                counts.updated,
                counts.skipped,
                counts.deactivated,
                duration_ms,
            )
            return CatalogSyncResult(
                catalog=catalog.value,
                cliente_id=cliente_id,
                database_name=database_name,
                status=CatalogSyncStatus.COMPLETED,
                counts=counts,
                duration_ms=duration_ms,
            )
        except CustomException as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            logger.warning(
                "Catalog sync failed catalog=%s cliente_id=%s database=%s code=%s",
                catalog.value,
                cliente_id,
                database_name,
                exc.internal_code,
            )
            return CatalogSyncResult(
                catalog=catalog.value,
                cliente_id=cliente_id,
                database_name=database_name,
                status=CatalogSyncStatus.FAILED,
                duration_ms=duration_ms,
                error=CatalogSyncErrorDetail(
                    internal_code=exc.internal_code or "CATALOG_SYNC_FAILED",
                    message=str(exc.detail),
                ),
            )
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            logger.exception(
                "Catalog sync unexpected error catalog=%s cliente_id=%s database=%s",
                catalog.value,
                cliente_id,
                database_name,
            )
            return CatalogSyncResult(
                catalog=catalog.value,
                cliente_id=cliente_id,
                database_name=database_name,
                status=CatalogSyncStatus.FAILED,
                duration_ms=duration_ms,
                error=CatalogSyncErrorDetail(
                    internal_code="CATALOG_SYNC_APPLY_FAILED",
                    message="Error inesperado sincronizando catálogo.",
                ),
            )


__all__ = ["CatalogSyncService"]
