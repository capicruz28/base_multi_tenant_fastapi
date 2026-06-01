"""Unit tests del runner smoke (sin HTTP real)."""
from scripts.lib.http_smoke_runner import SmokeReport, SmokeStepResult


def test_smoke_report_passed_when_all_ok():
    r = SmokeReport(subdominio="x", base_url="http://localhost:8000")
    r.steps = [
        SmokeStepResult("login", True, 200),
        SmokeStepResult("org_empresa_listar", True, 200),
    ]
    r.finished_at = r.started_at
    assert r.passed
    d = r.to_dict()
    assert d["passed"] is True
    assert len(d["steps"]) == 2


def test_smoke_report_fails_on_any_step():
    r = SmokeReport(subdominio="x", base_url="http://localhost:8000")
    r.steps = [
        SmokeStepResult("login", True, 200),
        SmokeStepResult("refresh", False, 401, "bad"),
    ]
    assert not r.passed
