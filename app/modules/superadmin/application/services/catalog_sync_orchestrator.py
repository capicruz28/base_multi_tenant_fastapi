"""Orquestación manual Product Reference sync — validación CP + modalidad A/B (F14)."""
from __future__ import annotations

import logging
import time
from typing import Optional
from uuid import UUID

from sqlalchemy import text

from app.core.catalog.catalog_sync_definitions import CatalogKind, get_catalog_definition
from app.core.catalog.catalog_sync_types import (
    CatalogSyncBatchResult,
    CatalogSyncBatchStatus,
    CatalogSyncCounts,
    CatalogSyncErrorDetail,
    CatalogSyncResult,
    CatalogSyncStatus,
    CatalogSyncTenantOutcome,
    DedicatedTenantTarget,
)
from app.core.exceptions import CustomException, DatabaseError, NotFoundError, ServiceError
from app.infrastructure.catalog.dedicated_catalog_writer import DedicatedCatalogWriter
from app.infrastructure.catalog.platform_catalog_reader import PlatformCatalogReader
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import execute_query
from app.modules.superadmin.application.services.catalog_sync_service import CatalogSyncService
from app.modules.tenant.application.provisioning import DEDICATED_INSTALLATION_TYPE
from app.modules.tenant.application.services.cliente_service import ClienteService
from app.modules.tenant.application.services.conexion_service import ConexionService

logger = logging.getLogger(__name__)


class CatalogSyncOrchestrator:
    """Validaciones Control Plane y delegación a CatalogSyncService."""

    def __init__(
        self,
        *,
        sync_service: Optional[CatalogSyncService] = None,
        reader: Optional[PlatformCatalogReader] = None,
        writer: Optional[DedicatedCatalogWriter] = None,
    ) -> None:
        self._reader = reader or PlatformCatalogReader()
        self._writer = writer or DedicatedCatalogWriter()
        self._sync_service = sync_service or CatalogSyncService(
            reader=self._reader,
            writer=self._writer,
        )

    async def sync_one(
        self,
        cliente_id: UUID,
        catalog: CatalogKind,
    ) -> CatalogSyncResult:
        target = await self._resolve_and_validate_target(cliente_id, catalog)
        result = await self._sync_service.run(
            cliente_id=target.cliente_id,
            catalog=catalog,
            database_name=target.database_name,
        )
        return CatalogSyncResult(
            catalog=result.catalog,
            cliente_id=result.cliente_id,
            database_name=result.database_name,
            status=result.status,
            codigo_cliente=target.codigo_cliente,
            razon_social=target.razon_social,
            counts=result.counts,
            duration_ms=result.duration_ms,
            error=result.error,
        )

    async def sync_all(
        self,
        catalog: CatalogKind,
        *,
        continue_on_error: bool = True,
    ) -> CatalogSyncBatchResult:
        started = time.perf_counter()
        tenants = await self._list_dedicated_targets()
        outcomes: list[CatalogSyncTenantOutcome] = []
        aggregated = CatalogSyncCounts()

        for tenant in tenants:
            tenant_started = time.perf_counter()
            try:
                await self._validate_target(tenant, catalog)
            except CustomException as exc:
                duration_ms = int((time.perf_counter() - tenant_started) * 1000)
                outcomes.append(
                    CatalogSyncTenantOutcome(
                        cliente_id=tenant.cliente_id,
                        codigo_cliente=tenant.codigo_cliente,
                        database_name=tenant.database_name,
                        razon_social=tenant.razon_social,
                        status=CatalogSyncStatus.FAILED,
                        duration_ms=duration_ms,
                        error=CatalogSyncErrorDetail(
                            internal_code=exc.internal_code or "CATALOG_SYNC_VALIDATION_FAILED",
                            message=str(exc.detail),
                        ),
                    )
                )
                if not continue_on_error:
                    break
                continue

            result = await self._sync_service.run(
                cliente_id=tenant.cliente_id,
                catalog=catalog,
                database_name=tenant.database_name,
            )
            duration_ms = int((time.perf_counter() - tenant_started) * 1000)
            if result.status == CatalogSyncStatus.COMPLETED and result.counts is not None:
                aggregated = CatalogSyncCounts(
                    inserted=aggregated.inserted + result.counts.inserted,
                    updated=aggregated.updated + result.counts.updated,
                    skipped=aggregated.skipped + result.counts.skipped,
                    deactivated=aggregated.deactivated + result.counts.deactivated,
                    platform_total=result.counts.platform_total,
                    dedicated_before=aggregated.dedicated_before,
                )
            outcomes.append(
                CatalogSyncTenantOutcome(
                    cliente_id=tenant.cliente_id,
                    codigo_cliente=tenant.codigo_cliente,
                    database_name=tenant.database_name,
                    razon_social=tenant.razon_social,
                    status=result.status,
                    counts=result.counts,
                    duration_ms=duration_ms,
                    error=result.error,
                )
            )
            if not continue_on_error and result.status == CatalogSyncStatus.FAILED:
                break

        tenants_completed = sum(
            1 for item in outcomes if item.status == CatalogSyncStatus.COMPLETED
        )
        tenants_failed = sum(
            1 for item in outcomes if item.status == CatalogSyncStatus.FAILED
        )
        batch_status = self._resolve_batch_status(
            tenants_total=len(tenants),
            tenants_completed=tenants_completed,
            tenants_failed=tenants_failed,
        )
        duration_ms = int((time.perf_counter() - started) * 1000)
        return CatalogSyncBatchResult(
            catalog=catalog.value,
            status=batch_status,
            tenants_total=len(tenants),
            tenants_completed=tenants_completed,
            tenants_failed=tenants_failed,
            aggregated_counts=aggregated,
            outcomes=tuple(outcomes),
            duration_ms=duration_ms,
        )

    async def _resolve_and_validate_target(
        self,
        cliente_id: UUID,
        catalog: CatalogKind,
    ) -> DedicatedTenantTarget:
        target = await self._load_target(cliente_id)
        await self._validate_target(target, catalog)
        return target

    async def _load_target(self, cliente_id: UUID) -> DedicatedTenantTarget:
        cliente = await ClienteService.obtener_cliente_por_id(cliente_id)
        if cliente is None:
            raise NotFoundError(
                detail="Cliente no encontrado.",
                internal_code="NOT_FOUND",
            )
        conexion = await ConexionService.obtener_conexion_principal(cliente_id)
        database_name = conexion.nombre_bd if conexion is not None else ""
        return DedicatedTenantTarget(
            cliente_id=cliente_id,
            codigo_cliente=str(cliente.codigo_cliente or ""),
            database_name=database_name or "",
            razon_social=str(cliente.razon_social or ""),
        )

    async def _validate_target(
        self,
        target: DedicatedTenantTarget,
        catalog: CatalogKind,
    ) -> None:
        cliente = await ClienteService.obtener_cliente_por_id(target.cliente_id)
        if cliente is None:
            raise NotFoundError(
                detail="Cliente no encontrado.",
                internal_code="NOT_FOUND",
            )
        if (cliente.tipo_instalacion or "").strip().lower() != DEDICATED_INSTALLATION_TYPE:
            raise ServiceError(
                status_code=422,
                detail="El cliente no es de tipo instalación dedicated.",
                internal_code="CLIENT_NOT_DEDICATED",
            )
        if not cliente.es_activo:
            raise ServiceError(
                status_code=422,
                detail="El cliente no está activo.",
                internal_code="CLIENT_INACTIVE",
            )
        if not target.database_name:
            raise ServiceError(
                status_code=422,
                detail="No existe conexión principal activa para el cliente dedicated.",
                internal_code="DEDICATED_CONNECTION_NOT_FOUND",
            )
        await self._writer.ping(target.database_name)
        await self._validate_fk_prerequisites(target.database_name, catalog)

    async def _validate_fk_prerequisites(
        self,
        database_name: str,
        catalog: CatalogKind,
    ) -> None:
        definition = get_catalog_definition(catalog)
        if definition.parent_kind is None or not definition.parent_fk_column:
            return

        parent_definition = get_catalog_definition(definition.parent_kind)
        required_fk_values = await self._reader.fetch_distinct_parent_fk_values(catalog)
        if not required_fk_values:
            return

        existing_parent_pks = await self._writer.existing_primary_keys(
            definition.parent_kind,
            database_name,
            sorted(required_fk_values),
        )
        missing = sorted(required_fk_values - existing_parent_pks)
        if not missing:
            return

        raise ServiceError(
            status_code=422,
            detail=(
                f"No se puede sincronizar {catalog.value}: faltan registros padre "
                f"en {parent_definition.table_name} ({parent_definition.primary_key})."
            ),
            internal_code="CATALOG_SYNC_FK_PREREQUISITE",
        )

    async def _list_dedicated_targets(self) -> list[DedicatedTenantTarget]:
        query = text(
            """
            SELECT
                c.cliente_id,
                c.codigo_cliente,
                c.razon_social,
                cc.nombre_bd
            FROM cliente c
            INNER JOIN cliente_conexion cc
                ON cc.cliente_id = c.cliente_id
            WHERE c.tipo_instalacion = :tipo_instalacion
              AND c.es_activo = 1
              AND cc.es_conexion_principal = 1
              AND cc.es_activo = 1
            ORDER BY c.codigo_cliente
            """
        ).bindparams(tipo_instalacion=DEDICATED_INSTALLATION_TYPE)
        try:
            rows = await execute_query(
                query,
                connection_type=DatabaseConnection.ADMIN,
                client_id=None,
            )
        except DatabaseError:
            raise
        except Exception as exc:
            raise DatabaseError(
                detail="Error listando clientes dedicated.",
                internal_code="PLATFORM_CATALOG_READ_FAILED",
            ) from exc

        targets: list[DedicatedTenantTarget] = []
        for row in rows:
            cliente_id = row["cliente_id"]
            if not isinstance(cliente_id, UUID):
                cliente_id = UUID(str(cliente_id))
            targets.append(
                DedicatedTenantTarget(
                    cliente_id=cliente_id,
                    codigo_cliente=str(row.get("codigo_cliente") or ""),
                    database_name=str(row.get("nombre_bd") or ""),
                    razon_social=str(row.get("razon_social") or ""),
                )
            )
        return targets

    @staticmethod
    def _resolve_batch_status(
        *,
        tenants_total: int,
        tenants_completed: int,
        tenants_failed: int,
    ) -> CatalogSyncBatchStatus:
        if tenants_total == 0 or tenants_failed == 0:
            return CatalogSyncBatchStatus.COMPLETED
        if tenants_completed == 0:
            return CatalogSyncBatchStatus.FAILED
        return CatalogSyncBatchStatus.PARTIAL


__all__ = ["CatalogSyncOrchestrator"]
