"""F8-A — E2E smoke Auth Runtime (Shared + Dedicated)."""
from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional

import httpx

BASE = "http://localhost:8000/api/v1"
TIMEOUT = 30.0

TENANTS = [
    {
        "name": "Shared (acme)",
        "subdominio": "acme",
        "username": "admin",
        "password": "admin123",
    },
    {
        "name": "Dedicated (acmec)",
        "subdominio": "acmec",
        "username": "admin",
        "password": "admin123",
    },
]


def _headers(subdominio: str, token: Optional[str] = None) -> Dict[str, str]:
    h = {
        "Origin": f"http://{subdominio}.app.local:8000",
        "X-Client-Type": "mobile",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _step(label: str, ok: bool, detail: str = "") -> Dict[str, Any]:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail else ""))
    return {"step": label, "status": status, "detail": detail}


def run_tenant(cfg: Dict[str, str]) -> Dict[str, Any]:
    sub = cfg["subdominio"]
    results: list[Dict[str, Any]] = []
    print(f"\n=== {cfg['name']} ===")

    with httpx.Client(base_url=BASE, timeout=TIMEOUT) as client:
        login = client.post(
            "/auth/login/",
            data={"username": cfg["username"], "password": cfg["password"]},
            headers=_headers(sub),
        )
        if login.status_code != 200:
            results.append(
                _step("Login", False, f"HTTP {login.status_code}: {login.text[:200]}")
            )
            return {"tenant": cfg["name"], "results": results, "overall": "FAIL"}

        body = login.json()
        access = body.get("access_token")
        refresh = body.get("refresh_token")
        results.append(_step("Login", bool(access and refresh)))

        me = client.get("/auth/me/", headers=_headers(sub, access))
        results.append(_step("/auth/me", me.status_code == 200, f"HTTP {me.status_code}"))

        perms = client.get("/auth/permissions/me", headers=_headers(sub, access))
        results.append(
            _step(
                "/auth/permissions/me",
                perms.status_code == 200,
                f"HTTP {perms.status_code}",
            )
        )

        menu = client.get("/auth/menu", headers=_headers(sub, access))
        results.append(
            _step("/auth/menu", menu.status_code == 200, f"HTTP {menu.status_code}")
        )

        refreshed = client.post(
            "/auth/refresh/",
            json={"refresh_token": refresh},
            headers=_headers(sub, access),
        )
        new_access = None
        new_refresh = None
        if refreshed.status_code == 200:
            rb = refreshed.json()
            new_access = rb.get("access_token")
            new_refresh = rb.get("refresh_token")
        results.append(
            _step("Refresh", refreshed.status_code == 200, f"HTTP {refreshed.status_code}")
        )

        token_for_logout = new_access or access
        refresh_for_logout = new_refresh or refresh

        logout = client.post(
            "/auth/logout/",
            json={"refresh_token": refresh_for_logout},
            headers=_headers(sub, token_for_logout),
        )
        results.append(_step("Logout", logout.status_code == 200, f"HTTP {logout.status_code}"))

        login2 = client.post(
            "/auth/login/",
            data={"username": cfg["username"], "password": cfg["password"]},
            headers=_headers(sub),
        )
        if login2.status_code != 200:
            results.append(_step("Login (logout-all prep)", False, f"HTTP {login2.status_code}"))
            overall = "FAIL" if any(r["status"] == "FAIL" for r in results) else "PASS"
            return {"tenant": cfg["name"], "results": results, "overall": overall}

        access2 = login2.json().get("access_token")
        refresh2 = login2.json().get("refresh_token")
        logout_all = client.post(
            "/auth/logout_all/",
            json={"refresh_token": refresh2},
            headers=_headers(sub, access2),
        )
        results.append(
            _step("Logout All", logout_all.status_code == 200, f"HTTP {logout_all.status_code}")
        )

        login3 = client.post(
            "/auth/login/",
            data={"username": cfg["username"], "password": cfg["password"]},
            headers=_headers(sub),
        )
        if login3.status_code == 200 and login3.json().get("empresas_disponibles"):
            empresas = login3.json()["empresas_disponibles"]
            if len(empresas) >= 1:
                eid = empresas[0].get("empresa_id")
                sel = client.post(
                    "/auth/seleccionar-empresa/",
                    json={"empresa_id": eid},
                    headers=_headers(sub, login3.json().get("access_token")),
                )
                results.append(
                    _step(
                        "Cambio empresa",
                        sel.status_code == 200,
                        f"HTTP {sel.status_code}",
                    )
                )
            else:
                results.append(_step("Cambio empresa", True, "sin empresas — skip"))
        else:
            results.append(_step("Cambio empresa", True, "login sin empresas — skip"))

    overall = "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL"
    return {"tenant": cfg["name"], "results": results, "overall": overall}


def main() -> int:
    print("F8-A Auth Runtime E2E — localhost:8000")
    summary = [run_tenant(t) for t in TENANTS]
    print("\n=== RESUMEN ===")
    for s in summary:
        print(f"{s['tenant']}: {s['overall']}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if all(s["overall"] == "PASS" for s in summary) else 1


if __name__ == "__main__":
    sys.exit(main())
