#!/usr/bin/env python3
"""
PR-F4-12 — Dedicated Provisioning E2E mock gate + evidencia G-F4-03.

Ejecuta tests/integration/test_hybrid_provisioning_* sin SQL Server.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

E2E_TARGETS = [
    "tests/integration/test_hybrid_provisioning_e2e.py",
]


def _run_e2e() -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *E2E_TARGETS,
        "-q",
        "--tb=line",
    ]
    env = os.environ.copy()
    env.setdefault("SKIP_DB_INTEGRATION_TESTS", "1")
    print("Running F4 provisioning E2E:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    output = (result.stdout or "") + (result.stderr or "")
    print(output)
    return result.returncode, output


def _parse_counts(output: str) -> dict:
    match = re.search(r"(\d+) passed", output)
    passed = int(match.group(1)) if match else 0
    failed_match = re.search(r"(\d+) failed", output)
    failed = int(failed_match.group(1)) if failed_match else 0
    return {"passed": passed, "failed": failed}


def _write_artifacts(exit_code: int, output: str) -> None:
    counts = _parse_counts(output)
    summary = {
        "artifact_type": "f4_provisioning_e2e_gate",
        "gate": "G-F4-03",
        "reference": "IP-2.0.1 F4-WP12 / DOD-F4-12",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "exit_code": exit_code,
        "passed": exit_code == 0,
        "test_counts": counts,
        "targets": E2E_TARGETS,
        "tag_preparation": "hybrid-gate-f4-complete",
    }
    (ROOT / "f4-provisioning-e2e-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    metrics_manifest = {
        "artifact_type": "f4_provisioning_metrics",
        "reference": "DEDICATED_PROVISIONING_API_CONTRACT.md §16 / DOD-F4-10",
        "description": "Cinco señales mínimas de ciclo de vida provisioning dedicated",
        "signals": {
            "dedicated.provisioning.started": {
                "when": "POST /clientes/ dedicated 201",
                "fields": ["cliente_id", "run_id", "actor_user_id"],
            },
            "dedicated.provisioning.step.completed": {
                "when": "Cada step saga OK",
                "fields": ["cliente_id", "run_id", "step_code"],
            },
            "dedicated.provisioning.ready": {
                "when": "S10 mark_ready",
                "fields": ["cliente_id", "run_id", "duration_seconds"],
            },
            "dedicated.provisioning.failed": {
                "when": "Estado failed / abort",
                "fields": ["cliente_id", "run_id", "error_code"],
            },
            "dedicated.provisioning.retry": {
                "when": "POST retry",
                "fields": ["cliente_id", "actor_user_id"],
            },
        },
        "staging_dashboard_note": "Exportar a Prometheus/Datadog en F5b; E2E mock valida contrato.",
    }
    manifest_path = ROOT / "docs" / "implementation" / "HYBRID_F4_PROVISIONING_METRICS_MANIFEST.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(metrics_manifest, indent=2) + "\n", encoding="utf-8")

    gf403 = {
        "artifact_type": "f4_gate_evidence_gf403",
        "gate": "G-F4-03",
        "status": "READY_FOR_SIGN_OFF" if exit_code == 0 else "BLOCKED",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "checklist": {
            "GF4-03-01": "PR-F4-10…12 merged (pending merge)",
            "GF4-03-02": "DOD-F4 completo (pending formal sign-off)",
            "GF4-03-03": f"E2E mock green: {exit_code == 0}",
            "GF4-03-04": "Métricas manifest committed",
            "GF4-03-08": "Runbook HYBRID_F4_PROVISIONING_RUNBOOK.md",
            "GF4-03-09": "Tag hybrid-gate-f4-complete (post-merge)",
        },
        "e2e_summary": summary,
    }
    (ROOT / "docs" / "implementation" / "HYBRID_F4_GATE_EVIDENCE_GF403.json").write_text(
        json.dumps(gf403, indent=2) + "\n",
        encoding="utf-8",
    )

    step_summary = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as fh:
            fh.write("## F4 Provisioning E2E (mock)\n\n")
            fh.write(f"- passed: {exit_code == 0}\n")
            fh.write(f"- tests passed: {counts['passed']}\n")
            fh.write(f"- tag prep: `hybrid-gate-f4-complete`\n")


def main() -> int:
    exit_code, output = _run_e2e()
    _write_artifacts(exit_code, output)
    if exit_code != 0:
        print("F4 provisioning E2E gate FAILED", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
