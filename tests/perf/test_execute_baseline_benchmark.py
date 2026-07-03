"""PR-F2-01 — execute_* baseline benchmark tests (F2-WP01)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.perf.execute_baseline_runner import (
    P95_REGRESSION_THRESHOLD_PCT,
    build_report,
    collect_baseline,
)

ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "docs" / "implementation" / "HYBRID_F2_EXECUTE_BASELINE.json"


@pytest.mark.slow
@pytest.mark.asyncio
async def test_collect_baseline_produces_all_scenarios():
    results = await collect_baseline(warmup=3, iterations=10)
    expected = {
        "execute_query_shared_cold_la",
        "execute_query_shared_warm_la",
        "execute_query_admin_control_plane",
        "get_connection_metadata_lb_hit",
        "get_connection_metadata_cold_path",
        "prepare_core_query_gateway",
    }
    assert set(results.keys()) == expected
    for result in results.values():
        assert result.samples == 10
        assert result.p50_ms >= 0
        assert result.p95_ms >= result.p50_ms


@pytest.mark.slow
@pytest.mark.shared_regression
def test_baseline_report_documents_p95_threshold():
    report = build_report({})
    assert report["threshold_p95_regression_pct"] == P95_REGRESSION_THRESHOLD_PCT
    assert report["artifact_type"] == "f2_execute_baseline"
    assert report["gate_target"] == "G-F2"


@pytest.mark.slow
def test_committed_baseline_json_exists_and_is_valid():
    if not BASELINE_JSON.exists():
        pytest.skip("Run scripts/benchmark_execute_baseline.py to generate baseline artifact")
    data = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    assert data["artifact_type"] == "f2_execute_baseline"
    assert len(data["scenarios"]) >= 6
    assert data["threshold_p95_regression_pct"] == P95_REGRESSION_THRESHOLD_PCT
