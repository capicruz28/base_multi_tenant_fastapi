#!/usr/bin/env python3
"""Prueba empírica: PUT cliente vía API live y verifica en qué BD quedó el UPDATE."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

import pyodbc

BASES = {
    "local": "http://127.0.0.1:8000",
    "docker": "http://localhost:8000",
}
BASE = BASES["local"]
CLIENTE_ID = "00000000-0000-0000-0000-000000000001"
MARKER = "#A0B1C2"
DBS = ["bd_caxis_saas", "bd_sistema_saas"]
def conn_str(db: str) -> str:
    return (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER=CARLOSPC;DATABASE={db};UID=soporte;PWD=rrhh03;"
        "TrustServerCertificate=yes;"
    )


def http_json(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json", "Host": "platform.app.local:8000"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def login_form(username: str, password: str) -> dict:
    body = urllib.parse.urlencode({"username": username, "password": password}).encode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "platform.app.local:8000",
    }
    req = urllib.request.Request(f"{BASE}/api/v1/auth/login/", data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def read_colors() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for db in DBS:
        cn = pyodbc.connect(conn_str(db))
        cur = cn.cursor()
        cur.execute(
            "SELECT color_primario FROM cliente WHERE cliente_id = ?",
            CLIENTE_ID,
        )
        row = cur.fetchone()
        out[db] = row[0] if row else None
        cn.close()
    return out


def run_target(name: str, base: str, marker: str) -> None:
    global BASE
    BASE = base
    print(f"\n########## TARGET: {name} ({base}) ##########")
    req = urllib.request.Request(f"{BASE}/debug-env")
    with urllib.request.urlopen(req, timeout=5) as resp:
        debug = json.loads(resp.read().decode())
    print(f"debug-env db_database={debug.get('db_database')} db_server={debug.get('db_server')}")

    before = read_colors()
    print("=== color_primario BEFORE ===")
    for db, color in before.items():
        print(f"  {db}: {color}")

    login = login_form("superadmin", "admin123")
    token = login["access_token"]
    print("=== login OK ===")

    updated = http_json(
        "PUT",
        f"/api/v1/clientes/{CLIENTE_ID}/",
        {"color_primario": marker},
        token=token,
    )
    data = updated.get("data") or updated
    print(f"=== API response color_primario = {data.get('color_primario')} ===")

    after = read_colors()
    print("=== color_primario AFTER ===")
    for db, color in after.items():
        changed = before[db] != after[db]
        print(f"  {db}: {color}  changed={changed}")


def main() -> None:
    run_target("LOCAL", BASES["local"], "#A0B1C2")
    run_target("DOCKER", BASES["docker"], "#D0E1F2")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}")
        raise
