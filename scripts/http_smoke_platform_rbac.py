#!/usr/bin/env python3
"""Smoke HTTP — operador plataforma (superadmin + Origin platform)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lib.http_smoke_runner import run_platform_smoke  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default=os.environ.get("SMOKE_BASE_URL", "http://localhost:8000"))
    p.add_argument("--username", default=os.environ.get("SMOKE_PLATFORM_USER", "superadmin"))
    p.add_argument("--password", default=os.environ.get("SMOKE_PLATFORM_PASSWORD", "admin123"))
    p.add_argument("--json-out", default=None)
    args = p.parse_args()

    report = run_platform_smoke(
        base_url=args.base_url.rstrip("/"),
        username=args.username,
        password=args.password,
    )
    text = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
    print(text)
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
