#!/usr/bin/env python3
"""
Validación funcional P2-001 — sort_by/sort_dir ORG/INV (staging).

Uso:
  python scripts/validate_p2_sort_staging.py
  python scripts/validate_p2_sort_staging.py --base-url http://localhost:8000 \\
    --subdominio innova --username admin --password admin123
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lib.http_smoke_client import HttpSmokeClient
from scripts.lib.http_smoke_runner import tenant_origin

EVIDENCE_PATH = (
    PROJECT_ROOT
    / "app/bootstrap_v2/00_manifest/evidence/P2_ORG_INV_SORT_VALIDATION.json"
)

P2_CASES = [
    ("inv_categorias_legacy_no_sort", "GET", "/api/v1/inv/categorias", None),
    ("inv_categorias_sort_nombre", "GET", "/api/v1/inv/categorias", {"sort_by": "nombre", "sort_dir": "asc"}),
    ("inv_categorias_sort_invalid", "GET", "/api/v1/inv/categorias", {"sort_by": "invalid_col"}),
    ("inv_categorias_sort_dir_ignored", "GET", "/api/v1/inv/categorias", {"sort_dir": "desc"}),
    ("inv_categorias_paginated_sort", "GET", "/api/v1/inv/categorias", {"page": "1", "limit": "10", "sort_by": "codigo", "sort_dir": "asc"}),
    ("inv_movimientos_sort_fecha", "GET", "/api/v1/inv/movimientos", {"page": "1", "limit": "5", "sort_by": "fecha_movimiento", "sort_dir": "desc"}),
    ("inv_productos_sort", "GET", "/api/v1/inv/productos", {"page": "1", "sort_by": "nombre", "sort_dir": "asc"}),
    ("inv_stock_sort", "GET", "/api/v1/inv/stock", {"page": "1", "sort_by": "cantidad_actual", "sort_dir": "desc"}),
    ("org_empresa_sort", "GET", "/api/v1/org/empresa", {"sort_by": "razon_social", "sort_dir": "asc"}),
    ("org_centros_sort", "GET", "/api/v1/org/centros-costo", {"page": "1", "sort_by": "codigo", "sort_dir": "asc"}),
    ("org_parametros_sort", "GET", "/api/v1/org/parametros", {"page": "1", "sort_by": "modulo_codigo", "sort_dir": "asc"}),
    ("org_parametros_sort_invalid", "GET", "/api/v1/org/parametros", {"sort_by": "bad_column"}),
]


def _tenant_login(
    client: HttpSmokeClient,
    *,
    subdominio: str,
    fe_port: str,
    username: str,
    password: str,
) -> Optional[str]:
    origin = tenant_origin(subdominio, fe_port)
    resp = client.request(
        "POST",
        "/api/v1/auth/login/",
        headers={"Origin": origin, "X-Client-Type": "mobile"},
        form_body={"username": username, "password": password},
    )
    if resp.status != 200 or not isinstance(resp.body, dict):
        return None
    access = resp.body.get("access_token")
    if access:
        return access
    selection = resp.body.get("selection_token")
    if not selection:
        return None
    empresas = resp.body.get("empresas_disponibles") or []
    if not empresas:
        return selection
    emp_id = empresas[0].get("empresa_id") or empresas[0].get("id")
    if not emp_id:
        return selection
    sel = client.request(
        "POST",
        "/api/v1/auth/empresa/seleccionar/",
        headers={"Origin": origin, "X-Client-Type": "mobile"},
        bearer=selection,
        json_body={"empresa_id": str(emp_id)},
    )
    if sel.status == 200 and isinstance(sel.body, dict) and sel.body.get("access_token"):
        return sel.body["access_token"]
    return selection


def _summarize(body: Any) -> Dict[str, Any]:
    if isinstance(body, list):
        return {"type": "list", "count": len(body)}
    if isinstance(body, dict) and "items" in body:
        return {
            "type": "paginated",
            "count": len(body.get("items") or []),
            "total": body.get("total"),
            "pagina_actual": body.get("pagina_actual"),
            "limit": body.get("limit"),
        }
    if isinstance(body, dict) and "detail" in body:
        return {"type": "error", "detail": body.get("detail")}
    return {"type": type(body).__name__}


def _openapi_sort_params(client: HttpSmokeClient) -> Dict[str, Any]:
    resp = client.request("GET", "/openapi.json")
    if resp.status != 200 or not isinstance(resp.body, dict):
        return {}
    paths = resp.body.get("paths") or {}
    out: Dict[str, Any] = {}
    for path in (
        "/api/v1/inv/categorias",
        "/api/v1/inv/movimientos",
        "/api/v1/org/empresa",
        "/api/v1/org/parametros",
    ):
        get_op = (paths.get(path) or {}).get("get") or {}
        params = [p.get("name") for p in get_op.get("parameters") or []]
        out[path] = {
            "params": params,
            "has_sort_by": "sort_by" in params,
            "has_sort_dir": "sort_dir" in params,
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="P2-001 sort staging validation")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--subdominio", default="innova")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    parser.add_argument("--fe-port", default="5173")
    parser.add_argument("--skip-http", action="store_true", help="Solo OpenAPI local si API no disponible")
    args = parser.parse_args()

    client = HttpSmokeClient(base_url=args.base_url)
    report: Dict[str, Any] = {
        "meta": {
            "tenant": args.subdominio,
            "phase": "P2-001",
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "cases": {},
        "openapi": {},
    }

    health = client.request("GET", "/health")
    api_up = health.status == 200

    if api_up and not args.skip_http:
        token = _tenant_login(
            client,
            subdominio=args.subdominio,
            fe_port=args.fe_port,
            username=args.username,
            password=args.password,
        )
        if not token:
            report["login"] = {"ok": False, "message": "No se pudo autenticar tenant"}
        else:
            report["login"] = {"ok": True}
            origin = tenant_origin(args.subdominio, args.fe_port)
            for name, method, path, query in P2_CASES:
                t0 = time.perf_counter()
                qs = ""
                if query:
                    qs = "?" + "&".join(f"{k}={v}" for k, v in query.items())
                resp = client.request(
                    method,
                    path + qs,
                    headers={"Origin": origin, "X-Client-Type": "mobile"},
                    bearer=token,
                )
                elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
                report["cases"][name] = {
                    "status": resp.status,
                    "ms": elapsed_ms,
                    "summary": _summarize(resp.body),
                    "path": path,
                    "query": query,
                }
    else:
        report["api_available"] = False

    if api_up:
        report["openapi"] = _openapi_sort_params(client)

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Evidencia: {EVIDENCE_PATH}")

    failures = []
    if report.get("login", {}).get("ok"):
        for name, case in report.get("cases", {}).items():
            if "invalid" in name:
                if case["status"] != 422:
                    failures.append(f"{name}: expected 422 got {case['status']}")
            elif case["status"] != 200:
                failures.append(f"{name}: expected 200 got {case['status']}")

    for path, info in report.get("openapi", {}).items():
        if not info.get("has_sort_by") or not info.get("has_sort_dir"):
            failures.append(f"OpenAPI {path}: missing sort params")

    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        return 1
    print("P2 staging validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
