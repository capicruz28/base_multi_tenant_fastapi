#!/usr/bin/env python3
"""
F2-WP01 / PR-F2-01 — Captura baseline de latencia execute_* (post-F1).

Uso:
    python scripts/benchmark_execute_baseline.py

Salida:
    docs/implementation/HYBRID_F2_EXECUTE_BASELINE.json
    docs/implementation/HYBRID_F2_EXECUTE_BASELINE.md
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.perf.execute_baseline_runner import run_and_write  # noqa: E402

JSON_OUT = ROOT / "docs" / "implementation" / "HYBRID_F2_EXECUTE_BASELINE.json"
MD_OUT = ROOT / "docs" / "implementation" / "HYBRID_F2_EXECUTE_BASELINE.md"


def main() -> int:
    commit_sha = os.environ.get("GITHUB_SHA", os.environ.get("GIT_COMMIT", ""))
    report = asyncio.run(
        run_and_write(
            json_path=JSON_OUT,
            markdown_path=MD_OUT,
            commit_sha=commit_sha,
        )
    )
    print(f"Baseline written: {JSON_OUT}")
    print(f"Summary written: {MD_OUT}")
    print(f"Scenarios: {len(report['scenarios'])}")
    for name, data in report["scenarios"].items():
        print(f"  {name}: p50={data['p50_ms']}ms p95={data['p95_ms']}ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
