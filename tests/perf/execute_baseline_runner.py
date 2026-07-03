"""
F2-WP01 — execute_* gateway latency baseline runner (PR-F2-01).

Mide overhead del pipeline gateway post-F1 con mocks (sin SQL Server).
Salida: métricas p50/p95 en ms por escenario + umbral acordado ±10% p95.
"""
from __future__ import annotations

import asyncio
import json
import platform
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from sqlalchemy import select

from app.core.tenant.cache import connection_cache
from app.core.tenant.routing import (
    clear_intra_request_route_cache,
    get_connection_metadata_async,
)
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import (
    _prepare_core_query_for_gateway,
    execute_query,
)
from app.infrastructure.database.tables import UsuarioTable
from tests.integration.helpers.hybrid_mock_metadata import (
    HYBRID_FIXTURE_TENANT_SHARED,
    build_shared_metadata,
)

DEFAULT_WARMUP = 10
DEFAULT_ITERATIONS = 100
P95_REGRESSION_THRESHOLD_PCT = 10

SHARED_CLIENT_ID = HYBRID_FIXTURE_TENANT_SHARED
SHARED_METADATA = build_shared_metadata(SHARED_CLIENT_ID)


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    samples: int
    mean_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "samples": self.samples,
            "mean_ms": round(self.mean_ms, 4),
            "p50_ms": round(self.p50_ms, 4),
            "p95_ms": round(self.p95_ms, 4),
            "p99_ms": round(self.p99_ms, 4),
            "min_ms": round(self.min_ms, 4),
            "max_ms": round(self.max_ms, 4),
        }


def _percentile(sorted_values: List[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def _summarize(name: str, durations_ms: List[float]) -> ScenarioResult:
    ordered = sorted(durations_ms)
    return ScenarioResult(
        name=name,
        samples=len(ordered),
        mean_ms=statistics.mean(ordered),
        p50_ms=_percentile(ordered, 50),
        p95_ms=_percentile(ordered, 95),
        p99_ms=_percentile(ordered, 99),
        min_ms=ordered[0],
        max_ms=ordered[-1],
    )


def _mock_async_session_cm():
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_result.keys.return_value = ["usuario_id"]
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    return mock_cm


def _reset_shared_gateway_caches() -> None:
    clear_intra_request_route_cache()
    connection_cache.invalidate(SHARED_CLIENT_ID)
    connection_cache.set(SHARED_CLIENT_ID, SHARED_METADATA.copy())


async def _bench_execute_query_shared_cold() -> None:
    """L-A cold por iteración; L-B pre-seeded (sin round-trip BD)."""
    clear_intra_request_route_cache()
    connection_cache.set(SHARED_CLIENT_ID, SHARED_METADATA.copy())
    mock_cm = _mock_async_session_cm()
    query = select(UsuarioTable).where(UsuarioTable.c.es_activo.is_(True))
    with patch(
        "app.infrastructure.database.connection_async.get_db_connection",
        return_value=mock_cm,
    ):
        await execute_query(query, client_id=SHARED_CLIENT_ID)


async def _bench_execute_query_shared_warm() -> None:
    """Mide execute_query con L-A ya poblado (sin reset intra-request)."""
    mock_cm = _mock_async_session_cm()
    query = select(UsuarioTable).where(UsuarioTable.c.es_activo.is_(True))
    with patch(
        "app.infrastructure.database.connection_async.get_db_connection",
        return_value=mock_cm,
    ):
        await execute_query(query, client_id=SHARED_CLIENT_ID)


async def _bench_execute_query_admin() -> None:
    mock_cm = _mock_async_session_cm()
    query = select(UsuarioTable).limit(1)
    with patch(
        "app.infrastructure.database.connection_async.get_db_connection",
        return_value=mock_cm,
    ):
        await execute_query(
            query,
            connection_type=DatabaseConnection.ADMIN,
            client_id=SHARED_CLIENT_ID,
        )


async def _bench_metadata_resolution(*, warm_la: bool) -> None:
    _reset_shared_gateway_caches()
    if not warm_la:
        with patch(
            "app.core.tenant.routing._query_connection_metadata_from_db_async",
            AsyncMock(return_value=None),
        ), patch(
            "app.infrastructure.database.connection_async.get_db_connection",
            side_effect=RuntimeError("simulated CP lookup for benchmark"),
        ):
            await get_connection_metadata_async(SHARED_CLIENT_ID)
    else:
        connection_cache.set(SHARED_CLIENT_ID, SHARED_METADATA.copy())
        await get_connection_metadata_async(SHARED_CLIENT_ID)


def _bench_prepare_core_query() -> None:
    query = select(UsuarioTable)
    _prepare_core_query_for_gateway(
        query,
        client_id=SHARED_CLIENT_ID,
        skip_tenant_validation=False,
    )


async def _scenario_execute_query_shared_cold() -> None:
    await _bench_execute_query_shared_cold()


async def _scenario_execute_query_shared_warm() -> None:
    await _bench_execute_query_shared_warm()


async def _scenario_execute_query_admin() -> None:
    await _bench_execute_query_admin()


async def _scenario_metadata_lb_hit() -> None:
    await _bench_metadata_resolution(warm_la=True)


async def _scenario_metadata_cold_path() -> None:
    await _bench_metadata_resolution(warm_la=False)


def _scenario_prepare_core_query() -> None:
    _bench_prepare_core_query()


async def _run_async_scenario(fn: Callable[[], Any], iterations: int) -> List[float]:
    durations: List[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        await fn()
        durations.append((time.perf_counter() - start) * 1000.0)
    return durations


def _run_sync_scenario(fn: Callable[[], Any], iterations: int) -> List[float]:
    durations: List[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        durations.append((time.perf_counter() - start) * 1000.0)
    return durations


async def collect_baseline(
    *,
    warmup: int = DEFAULT_WARMUP,
    iterations: int = DEFAULT_ITERATIONS,
) -> Dict[str, ScenarioResult]:
    scenarios: Dict[str, Callable[[], Any]] = {
        "execute_query_shared_cold_la": _scenario_execute_query_shared_cold,
        "execute_query_shared_warm_la": _scenario_execute_query_shared_warm,
        "execute_query_admin_control_plane": _scenario_execute_query_admin,
        "get_connection_metadata_lb_hit": _scenario_metadata_lb_hit,
        "get_connection_metadata_cold_path": _scenario_metadata_cold_path,
        "prepare_core_query_gateway": _scenario_prepare_core_query,
    }

    results: Dict[str, ScenarioResult] = {}
    for name, fn in scenarios.items():
        is_async = asyncio.iscoroutinefunction(fn)
        if name == "execute_query_shared_warm_la" and is_async:
            _reset_shared_gateway_caches()
            connection_cache.set(SHARED_CLIENT_ID, SHARED_METADATA.copy())
            await _bench_execute_query_shared_warm()
        for _ in range(warmup):
            if is_async:
                await fn()
            else:
                fn()
        if is_async:
            durations = await _run_async_scenario(fn, iterations)
        else:
            durations = _run_sync_scenario(fn, iterations)
        results[name] = _summarize(name, durations)
    return results


def build_report(
    scenario_results: Dict[str, ScenarioResult],
    *,
    commit_sha: str = "",
) -> Dict[str, Any]:
    return {
        "artifact_type": "f2_execute_baseline",
        "baseline_version": "BL-1.0",
        "ip_version": "IP-1.0",
        "gate_target": "G-F2",
        "pr": "PR-F2-01",
        "work_package": "F2-WP01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commit_sha": commit_sha,
        "threshold_p95_regression_pct": P95_REGRESSION_THRESHOLD_PCT,
        "methodology": {
            "warmup_iterations": DEFAULT_WARMUP,
            "measure_iterations": DEFAULT_ITERATIONS,
            "unit": "milliseconds",
            "database": "mocked (no SQL Server)",
            "scope": "execute_* gateway pipeline post-F1",
        },
        "environment": {
            "python_version": sys.version,
            "platform": platform.platform(),
        },
        "scenarios": {
            name: result.as_dict() for name, result in scenario_results.items()
        },
    }


def render_markdown_report(report: Dict[str, Any]) -> str:
    lines = [
        "# Hybrid Platform — execute_* Baseline (F2-WP01 / PR-F2-01)",
        "",
        f"- **Timestamp (UTC):** {report['timestamp']}",
        f"- **Gate target:** {report['gate_target']}",
        f"- **p95 regression threshold:** ±{report['threshold_p95_regression_pct']}%",
        f"- **Methodology:** {report['methodology']['warmup_iterations']} warmup + "
        f"{report['methodology']['measure_iterations']} measured iterations (mocked I/O)",
        "",
        "## Scenarios",
        "",
        "| Scenario | p50 (ms) | p95 (ms) | p99 (ms) | mean (ms) |",
        "|----------|----------|----------|----------|-----------|",
    ]
    for _name, data in report["scenarios"].items():
        lines.append(
            f"| {data['name']} | {data['p50_ms']} | {data['p95_ms']} | "
            f"{data['p99_ms']} | {data['mean_ms']} |"
        )
    lines.extend(
        [
            "",
            "## Usage",
            "",
            "Compare future runs against this baseline; **pass** if each scenario p95 "
            f"remains within ±{report['threshold_p95_regression_pct']}% (GF2-03 / DOD-F2-02).",
            "",
            "Regenerate:",
            "",
            "```bash",
            "python scripts/benchmark_execute_baseline.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(
    report: Dict[str, Any],
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown_report(report), encoding="utf-8")


async def run_and_write(
    *,
    json_path: Path,
    markdown_path: Path,
    commit_sha: str = "",
    warmup: int = DEFAULT_WARMUP,
    iterations: int = DEFAULT_ITERATIONS,
) -> Dict[str, Any]:
    results = await collect_baseline(warmup=warmup, iterations=iterations)
    report = build_report(results, commit_sha=commit_sha)
    write_report(report, json_path=json_path, markdown_path=markdown_path)
    return report
