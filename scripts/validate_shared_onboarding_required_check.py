#!/usr/bin/env python3
"""
PR-F4-12 — SHARED_ONBOARDING_REQUIRED_CHECK CI gate (IP-2.0.1 §10.1).

Regresión onboarding shared obligatoria en todo merge F4 desde F4-07.
Complementa (no reemplaza) shared-regression (G-02 / F2).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SHARED_ONBOARDING_TARGETS = [
    "tests/unit/test_onboarding_rbac_bootstrap.py",
    "tests/unit/test_onboarding_menu_bootstrap.py",
    "tests/unit/test_minimal_erp_tenant_bootstrap.py",
    "tests/unit/test_platform_identity_bootstrap.py",
    "tests/unit/test_tenant_exception_propagation.py",
    "tests/unit/test_base_operative_t1.py",
]


def _run_suite() -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *SHARED_ONBOARDING_TARGETS,
        "-q",
        "--tb=line",
    ]
    print("Running SHARED_ONBOARDING_REQUIRED_CHECK:", " ".join(cmd))
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    print(output)
    return result.returncode, output


def _write_summary(exit_code: int, output: str) -> None:
    summary = {
        "artifact_type": "f4_shared_onboarding_required_check",
        "gate": "SHARED_ONBOARDING_REQUIRED_CHECK",
        "reference": "IP-2.0.1 §10.1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "exit_code": exit_code,
        "passed": exit_code == 0,
        "targets": SHARED_ONBOARDING_TARGETS,
        "output_tail": output[-4000:] if output else "",
    }
    out_path = ROOT / "f4-shared-onboarding-check-summary.json"
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")

    step_summary = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as fh:
            fh.write("## F4 SHARED_ONBOARDING_REQUIRED_CHECK\n\n")
            fh.write(f"- passed: {exit_code == 0}\n")
            fh.write(f"- targets: {len(SHARED_ONBOARDING_TARGETS)} files\n")


def main() -> int:
    exit_code, output = _run_suite()
    _write_summary(exit_code, output)
    if exit_code != 0:
        print("SHARED_ONBOARDING_REQUIRED_CHECK FAILED", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
