#!/usr/bin/env python3
"""
F2-WP02 / PR-F2-02 — Shared regression CI gate (G-02 / G-F2).

Fase 1: suite Shared (mismo alcance que F0 shared-baseline-capture) — 100% pass.
Fase 2: p95 execute_* vs baseline PR-F2-01 (±threshold committed JSON).

Uso:
    python scripts/validate_shared_regression.py
    python scripts/validate_shared_regression.py --benchmark-only
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
BASELINE_JSON = ROOT / "docs" / "implementation" / "HYBRID_F2_EXECUTE_BASELINE.json"

SHARED_PYTEST_TARGETS = [
    "tests/unit/",
    "tests/integration/",
    "--ignore=tests/integration/test_hybrid_wrong_route.py",
    "--ignore=tests/integration/test_hybrid_tenant_isolation.py",
    "--ignore=tests/integration/test_hybrid_impersonation_harness.py",
]


def _run_shared_suite() -> int:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *SHARED_PYTEST_TARGETS,
        "-q",
        "--tb=line",
    ]
    print("Running shared suite:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT, env=os.environ.copy())
    return result.returncode


def _load_baseline() -> dict:
    if not BASELINE_JSON.is_file():
        raise FileNotFoundError(f"Baseline not found: {BASELINE_JSON}")
    data = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    if data.get("artifact_type") != "f2_execute_baseline":
        raise ValueError("Invalid baseline artifact_type")
    return data


def _compare_benchmark_p95() -> List[str]:
    from tests.perf.execute_baseline_runner import (
        DEFAULT_ITERATIONS,
        DEFAULT_WARMUP,
        collect_baseline,
    )

    baseline = _load_baseline()
    threshold_pct = float(baseline["threshold_p95_regression_pct"])
    max_factor = 1.0 + (threshold_pct / 100.0)
    reference = baseline["scenarios"]

    current = asyncio.run(
        collect_baseline(warmup=DEFAULT_WARMUP, iterations=DEFAULT_ITERATIONS)
    )

    errors: List[str] = []
    for name, ref in reference.items():
        if name not in current:
            errors.append(f"missing scenario {name!r}")
            continue
        ref_p95 = float(ref["p95_ms"])
        cur_p95 = current[name].p95_ms
        limit = ref_p95 * max_factor
        if cur_p95 > limit:
            errors.append(
                f"{name}: p95={cur_p95:.4f}ms exceeds limit={limit:.4f}ms "
                f"(baseline p95={ref_p95}ms + {threshold_pct:g}%)"
            )
        else:
            print(
                f"  OK {name}: p95={cur_p95:.4f}ms "
                f"(baseline={ref_p95}ms, limit={limit:.4f}ms)"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Shared regression gate (F2-WP02)")
    parser.add_argument(
        "--benchmark-only",
        action="store_true",
        help="Skip pytest suite; only compare execute_* p95 to F2 baseline",
    )
    args = parser.parse_args()

    if not args.benchmark_only:
        print("=== Phase 1/2: Shared test suite (G-02) ===")
        suite_rc = _run_shared_suite()
        if suite_rc != 0:
            print(f"FAIL: shared suite exit code {suite_rc}")
            return suite_rc
        print("PASS: shared test suite")

    print("=== Phase 2/2: execute_* p95 vs F2-WP01 baseline ===")
    try:
        bench_errors = _compare_benchmark_p95()
    except (FileNotFoundError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1

    if bench_errors:
        for msg in bench_errors:
            print(f"FAIL: {msg}")
        return 1

    print("PASS: shared-regression gate (G-02 / G-F2)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
