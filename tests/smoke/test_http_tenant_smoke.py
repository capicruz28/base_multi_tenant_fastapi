"""
Smoke HTTP — pytest wrapper (opcional, requiere API + credenciales).

Variables de entorno:
  SMOKE_BASE_URL, SMOKE_SUBDOMINIO, SMOKE_USERNAME, SMOKE_PASSWORD

Sin variables → tests skipped (CI unit-only no falla).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.http_smoke_runner import run_tenant_smoke  # noqa: E402


def _smoke_configured() -> bool:
    return bool(
        os.environ.get("SMOKE_BASE_URL")
        and os.environ.get("SMOKE_SUBDOMINIO")
        and os.environ.get("SMOKE_PASSWORD")
    )


@pytest.mark.smoke
@pytest.mark.skipif(not _smoke_configured(), reason="SMOKE_* env no configurado")
def test_tenant_http_smoke_suite():
    report = run_tenant_smoke(
        base_url=os.environ["SMOKE_BASE_URL"].rstrip("/"),
        subdominio=os.environ["SMOKE_SUBDOMINIO"],
        username=os.environ.get("SMOKE_USERNAME", "admin"),
        password=os.environ["SMOKE_PASSWORD"],
        fe_port=os.environ.get("SMOKE_FE_PORT", "5173"),
    )
    assert report.passed, report.to_dict()
