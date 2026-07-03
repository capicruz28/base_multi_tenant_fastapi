"""Motor puro de diff Product Reference — F14 Catalog Sync."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from app.core.catalog.catalog_sync_definitions import (
    CatalogDefinition,
    canonical_primary_key,
    extract_compare_payload,
    normalize_row_for_compare,
)
from app.core.catalog.catalog_sync_types import SyncAction, SyncPlan, SyncPlanEntry


def rows_compare_equal(
    platform_row: Mapping[str, Any],
    dedicated_row: Mapping[str, Any],
    definition: CatalogDefinition,
) -> bool:
    platform_norm = normalize_row_for_compare(platform_row, definition)
    dedicated_norm = normalize_row_for_compare(dedicated_row, definition)
    return platform_norm == dedicated_norm


def compute_sync_plan(
    *,
    platform_rows: Sequence[Mapping[str, Any]],
    dedicated_rows: Sequence[Mapping[str, Any]],
    definition: CatalogDefinition,
) -> SyncPlan:
    dedicated_by_pk: dict[str, Mapping[str, Any]] = {}
    for row in dedicated_rows:
        pk = canonical_primary_key(row, definition)
        if pk:
            dedicated_by_pk[pk] = row

    platform_pks: set[str] = set()
    entries: list[SyncPlanEntry] = []

    for platform_row in platform_rows:
        pk = canonical_primary_key(platform_row, definition)
        if not pk:
            continue
        platform_pks.add(pk)
        dedicated_row = dedicated_by_pk.get(pk)
        if dedicated_row is None:
            entries.append(
                SyncPlanEntry(
                    action=SyncAction.INSERT,
                    primary_key=pk,
                    payload=extract_compare_payload(platform_row, definition),
                )
            )
            continue
        if rows_compare_equal(platform_row, dedicated_row, definition):
            entries.append(
                SyncPlanEntry(
                    action=SyncAction.SKIP,
                    primary_key=pk,
                )
            )
            continue
        entries.append(
            SyncPlanEntry(
                action=SyncAction.UPDATE,
                primary_key=pk,
                payload=extract_compare_payload(platform_row, definition),
            )
        )

    for pk, dedicated_row in dedicated_by_pk.items():
        if pk in platform_pks:
            continue
        entries.append(
            SyncPlanEntry(
                action=SyncAction.SOFT_DEACTIVATE,
                primary_key=pk,
                payload=extract_compare_payload(dedicated_row, definition),
            )
        )

    return SyncPlan(catalog=definition.kind.value, entries=tuple(entries))


def summarize_sync_plan(plan: SyncPlan) -> dict[str, int]:
    counts = {
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "deactivated": 0,
    }
    for entry in plan.entries:
        if entry.action == SyncAction.INSERT:
            counts["inserted"] += 1
        elif entry.action == SyncAction.UPDATE:
            counts["updated"] += 1
        elif entry.action == SyncAction.SKIP:
            counts["skipped"] += 1
        elif entry.action == SyncAction.SOFT_DEACTIVATE:
            counts["deactivated"] += 1
    return counts


__all__ = [
    "compute_sync_plan",
    "rows_compare_equal",
    "summarize_sync_plan",
]
