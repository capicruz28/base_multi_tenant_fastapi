"""Smoke HTTP F13-C4 — Platform tenant_data wire-up."""
from __future__ import annotations

import asyncio
import sys

import httpx

BASE = "http://localhost:8000/api/v1"


async def login(sub: str, user: str, pwd: str) -> str:
    async with httpx.AsyncClient(base_url=BASE, timeout=30) as client:
        response = await client.post(
            "/auth/login/",
            json={"nombre_usuario": user, "contrasena": pwd},
            headers={"Host": f"{sub}.app.local"},
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def main() -> int:
    results: list[tuple] = []
    all_pass = True

    async def record(name: str, ok: bool, detail: str = "") -> None:
        nonlocal all_pass
        if not ok:
            all_pass = False
        results.append((name, "PASS" if ok else "FAIL", detail))

    # 1 Shared tenant
    try:
        token = await login("acme", "admin", "admin123")
        headers = {"Authorization": f"Bearer {token}", "Host": "acme.app.local"}
        async with httpx.AsyncClient(base_url=BASE, timeout=30, headers=headers) as client:
            me = (await client.get("/auth/me/")).json()
            stats = (await client.get(f"/clientes/{me['cliente_id']}/estadisticas/")).json()
            ok = stats.get("total_usuarios", 0) >= 1 and stats.get("modulos_activos", 0) >= 1
            await record("shared_estadisticas", ok, str(stats))
    except Exception as exc:
        await record("shared_estadisticas", False, str(exc)[:120])

    # 2 Dedicated tenant
    try:
        token = await login("acce", "admin", "Admin123!")
        headers = {"Authorization": f"Bearer {token}", "Host": "acce.app.local"}
        async with httpx.AsyncClient(base_url=BASE, timeout=30, headers=headers) as client:
            me = (await client.get("/auth/me/")).json()
            stats = (await client.get(f"/clientes/{me['cliente_id']}/estadisticas/")).json()
            ok = stats.get("total_usuarios", 0) >= 1 and stats.get("modulos_activos", 0) >= 1
            await record("dedicated_estadisticas", ok, str(stats))
    except Exception as exc:
        await record("dedicated_estadisticas", False, str(exc)[:120])

    # 3 Platform admin drill-down dedicated
    try:
        token = await login("platform", "superadmin", "admin123")
        headers = {"Authorization": f"Bearer {token}", "Host": "platform.app.local"}
        async with httpx.AsyncClient(base_url=BASE, timeout=30, headers=headers) as client:
            listed = (await client.get("/clientes/", params={"limit": 25})).json()
            items = listed if isinstance(listed, list) else listed.get("items", listed)
            acce = next((x for x in items if x.get("subdominio") == "acce"), None)
            if not acce:
                await record("platform_acce_stats", False, "acce not found")
            else:
                cid = acce["cliente_id"]
                stats = (await client.get(f"/clientes/{cid}/estadisticas/")).json()
                mods = (await client.get(f"/cliente-modulo/cliente/{cid}/")).json()
                mod_count = len(mods.get("data", []))
                ok = stats.get("total_usuarios", 0) >= 1 and stats.get("modulos_activos", 0) >= 1
                await record("platform_acce_stats", ok, f"users={stats.get('total_usuarios')} mods={stats.get('modulos_activos')}")
                await record("platform_acce_modulos", mod_count >= 1, f"count={mod_count}")
    except Exception as exc:
        await record("platform_acce_stats", False, str(exc)[:120])

    # 4 Impersonation dedicated permissions count
    try:
        token = await login("platform", "superadmin", "admin123")
        headers = {"Authorization": f"Bearer {token}", "Host": "platform.app.local"}
        async with httpx.AsyncClient(base_url=BASE, timeout=30, headers=headers) as client:
            listed = (await client.get("/clientes/", params={"limit": 25})).json()
            items = listed if isinstance(listed, list) else listed.get("items", listed)
            acce = next((x for x in items if x.get("subdominio") == "acce"), None)
            imp = await client.post(
                "/auth/impersonate/",
                json={"cliente_id": acce["cliente_id"], "effective_scope": "tenant"},
            )
            imp.raise_for_status()
            imp_token = imp.json()["access_token"]
            imp_headers = {
                "Authorization": f"Bearer {imp_token}",
                "Host": "platform.app.local",
            }
            perms = (await client.get("/auth/permissions/me/", headers=imp_headers)).json()
            codes = perms if isinstance(perms, list) else perms.get("permisos", perms)
            count = len(codes) if isinstance(codes, list) else len(codes.get("codes", []))
            await record("impersonation_dedicated_permissions", count >= 50, f"count={count}")
    except Exception as exc:
        await record("impersonation_dedicated_permissions", False, str(exc)[:120])

    for name, status, detail in results:
        print(f"{name}: {status} {detail}")
    print(f"all_passed={all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
