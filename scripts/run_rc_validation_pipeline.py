#!/usr/bin/env python3
"""
Pipeline mínimo de validación Release Candidate.

Modos:
  --unit-only          pytest unitarios RBAC/runtime (default CI)
  --http-smoke         smoke HTTP contra API en marcha (requiere credenciales)
  --full-staging       unit + health + onboarding opcional + smoke

Flujo objetivo (staging manual / automatizable):
  BD vacía → bootstrap SQL (ver STAGING_VALIDATION_PIPELINE.md)
  → startup app (permission_sync)
  → onboarding (--create-tenant o POST /clientes/)
  → smoke HTTP → PASS

Uso:
  python scripts/run_rc_validation_pipeline.py --unit-only
  python scripts/run_rc_validation_pipeline.py --http-smoke \\
    --subdominio prueba --username admin --password admin123
  python scripts/run_rc_validation_pipeline.py --full-staging --create-tenant
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lib.http_smoke_client import HttpSmokeClient
from scripts.lib.http_smoke_runner import platform_origin, run_tenant_smoke, tenant_origin

RC_UNIT_TESTS = [
    "tests/unit/test_core_permission_sync.py",
    "tests/unit/test_onboarding_rbac_bootstrap.py",
    "tests/unit/test_onboarding_menu_bootstrap.py",
    "tests/unit/test_menu_route_normalizer.py",
    "tests/unit/test_minimal_erp_tenant_bootstrap.py",
    "tests/unit/test_login_user_data_serialization.py",
    "tests/unit/test_legacy_tenant_rbac_repair.py",
]

# Cluster 8 — suite §12.2 RC2 (IAM Session V2)
RC_IAM_V2_UNIT_GLOB = "tests/unit/test_iam_sessions_v2_*"
RC_IAM_V2_INTEGRATION_GLOB = "tests/integration/test_iam_sessions_v2_*"
RC_IAM_V2_LEGACY_UNIT = [
    "tests/unit/test_iam_sessions_pa001.py",
    "tests/unit/test_iam_sessions_rc1.py",
    "tests/unit/test_iam_sessions_v1_enterprise.py",
]


def _run_pytest(files: list[str]) -> int:
    cmd = [sys.executable, "-m", "pytest", *files, "-q", "--tb=line"]
    print(">>", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(PROJECT_ROOT))


def _run_pytest_glob(pattern: str) -> int:
    files = sorted(str(p) for p in PROJECT_ROOT.glob(pattern))
    if not files:
        print(f"WARN: sin archivos para patrón {pattern!r}")
        return 0
    return _run_pytest(files)


def _run_iam_v2_rc2_suite() -> int:
    """Suite canónica §12.2 — RC2-04/05/06."""
    code = _run_pytest_glob(RC_IAM_V2_UNIT_GLOB)
    if code != 0:
        return code
    code = _run_pytest_glob(RC_IAM_V2_INTEGRATION_GLOB)
    if code != 0:
        return code
    return _run_pytest(RC_IAM_V2_LEGACY_UNIT)


def _health_ok(base_url: str, timeout: float = 5.0) -> bool:
    client = HttpSmokeClient(base_url=base_url, timeout_sec=timeout)
    for path in ("/health", "/api/v1/health"):
        try:
            resp = client.request("GET", path)
            if resp.status == 200:
                return True
        except Exception:
            continue
    return False


def _platform_login(
    base_url: str,
    *,
    username: str,
    password: str,
    fe_port: str,
) -> str | None:
    client = HttpSmokeClient(base_url=base_url)
    resp = client.request(
        "POST",
        "/api/v1/auth/login/",
        headers={
            "Origin": platform_origin(fe_port),
            "X-Client-Type": "mobile",
        },
        form_body={"username": username, "password": password},
    )
    if resp.status != 200 or not isinstance(resp.body, dict):
        return None
    return resp.body.get("access_token")


def _create_tenant_via_api(
    base_url: str,
    *,
    platform_token: str,
    fe_port: str,
) -> dict | None:
    suffix = uuid.uuid4().hex[:8]
    subdominio = f"smokerc{suffix}"
    codigo = f"SRC{suffix.upper()[:6]}"
    payload = {
        "codigo_cliente": codigo,
        "subdominio": subdominio,
        "razon_social": f"Smoke RC Tenant {suffix}",
        "nombre_comercial": f"SmokeRC {suffix}",
        "ruc": "20123456789",
        "tipo_instalacion": "shared",
        "modo_autenticacion": "local",
        "contacto_email": f"admin+{suffix}@smoke-rc.local",
        "contacto_nombre": "Smoke Admin",
        "plan_suscripcion": "trial",
        "estado_suscripcion": "activo",
        "es_activo": True,
        "es_demo": True,
    }
    client = HttpSmokeClient(base_url=base_url)
    resp = client.request(
        "POST",
        "/api/v1/clientes/",
        headers={
            "Origin": platform_origin(fe_port),
            "X-Client-Type": "mobile",
            "Authorization": f"Bearer {platform_token}",
        },
        json_body=payload,
    )
    if resp.status not in (200, 201) or not isinstance(resp.body, dict):
        return {"error": resp.status, "body": resp.body}
    cred = resp.body.get("credenciales_iniciales") or {}
    return {
        "subdominio": subdominio,
        "cliente_id": resp.body.get("data", {}).get("cliente_id"),
        "username": cred.get("nombre_usuario", "admin"),
        "password": cred.get("contrasena"),
        "raw": resp.body,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="RC validation pipeline")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--unit-only", action="store_true", help="Solo pytest unitarios")
    mode.add_argument("--http-smoke", action="store_true", help="Solo smoke HTTP")
    mode.add_argument("--full-staging", action="store_true", help="Unit + health + opcional tenant + smoke")
    mode.add_argument(
        "--iam-v2-rc2",
        action="store_true",
        help="Suite Cluster 8 §12.2 (unit V2 + integration IAM V2 + legacy V1)",
    )
    parser.add_argument("--base-url", default=os.environ.get("SMOKE_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--subdominio", default=os.environ.get("SMOKE_SUBDOMINIO"))
    parser.add_argument("--username", default=os.environ.get("SMOKE_USERNAME", "admin"))
    parser.add_argument("--password", default=os.environ.get("SMOKE_PASSWORD"))
    parser.add_argument("--fe-port", default=os.environ.get("SMOKE_FE_PORT", "5173"))
    parser.add_argument("--create-tenant", action="store_true", help="Crear tenant vía API (full-staging)")
    parser.add_argument("--platform-user", default=os.environ.get("SMOKE_PLATFORM_USER", "superadmin"))
    parser.add_argument("--platform-password", default=os.environ.get("SMOKE_PLATFORM_PASSWORD", "admin123"))
    parser.add_argument("--json-out", default=None)
    parser.add_argument("--skip-unit", action="store_true")
    args = parser.parse_args()

    if not (args.unit_only or args.http_smoke or args.full_staging or args.iam_v2_rc2):
        args.unit_only = True

    report: dict = {
        "mode": (
            "iam-v2-rc2"
            if args.iam_v2_rc2
            else (
                "unit-only"
                if args.unit_only
                else ("http-smoke" if args.http_smoke else "full-staging")
            )
        )
    }

    if args.iam_v2_rc2:
        code = _run_iam_v2_rc2_suite()
        report["iam_v2_rc2_exit_code"] = code
        print(json.dumps(report, indent=2))
        return code

    if args.unit_only or args.full_staging:
        if not args.skip_unit:
            code = _run_pytest(RC_UNIT_TESTS)
            report["unit_pytest_exit_code"] = code
            if code != 0:
                print(json.dumps(report, indent=2))
                return code
        else:
            report["unit_pytest"] = "skipped"

    if args.unit_only:
        print(json.dumps(report, indent=2))
        return 0

    base = args.base_url.rstrip("/")
    if not _health_ok(base):
        report["health"] = False
        print(json.dumps(report, indent=2))
        print("ERROR: API no responde en /health", file=sys.stderr)
        return 2
    report["health"] = True

    subdominio = args.subdominio
    username = args.username
    password = args.password

    if args.create_tenant or (args.full_staging and not subdominio):
        token = _platform_login(
            base,
            username=args.platform_user,
            password=args.platform_password,
            fe_port=args.fe_port,
        )
        if not token:
            report["onboarding"] = {"ok": False, "detail": "platform login failed"}
            print(json.dumps(report, indent=2))
            return 3
        created = _create_tenant_via_api(base, platform_token=token, fe_port=args.fe_port)
        report["onboarding"] = created
        if not created or not created.get("password"):
            print(json.dumps(report, indent=2))
            return 3
        subdominio = created["subdominio"]
        username = created["username"]
        password = created["password"]
        time.sleep(0.5)

    if not subdominio or not password:
        print("ERROR: --subdominio y --password requeridos para smoke", file=sys.stderr)
        return 4

    smoke = run_tenant_smoke(
        base_url=base,
        subdominio=subdominio,
        username=username,
        password=password,
        fe_port=args.fe_port,
    )
    report["smoke"] = smoke.to_dict()
    report["smoke_subdominio"] = subdominio
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")

    return 0 if smoke.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
