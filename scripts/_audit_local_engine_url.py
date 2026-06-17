#!/usr/bin/env python3
"""Inferencia del engine ADMIN del uvicorn local via debug-env + builder."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from urllib.parse import quote_plus

BASE_LOCAL = "http://127.0.0.1:8000"
BASE_DOCKER = "http://localhost:8000"


def fetch_debug(base: str) -> dict:
    req = urllib.request.Request(f"{base}/debug-env")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())


def admin_url_from_debug(d: dict, password: str = "***") -> str:
    # debug-env no expone DB_ADMIN_*; asumimos paridad con DB_* del mismo proceso
    user = d["db_user"]
    server = d["db_server"]
    port = d["db_port"]
    database = d["db_database"]
    driver = "ODBC Driver 17 for SQL Server"
    return (
        f"mssql+aioodbc://{quote_plus(user)}:{quote_plus(password)}@"
        f"{server}:{port}/{database}?"
        f"TrustServerCertificate=yes&driver={quote_plus(driver)}"
    )


def main() -> None:
    for label, base in [("LOCAL 127.0.0.1", BASE_LOCAL), ("DOCKER localhost", BASE_DOCKER)]:
        try:
            d = fetch_debug(base)
            print(f"=== {label} ===")
            print(json.dumps(d, indent=2))
            print(f"engine.url (ADMIN builder equivalent) = {admin_url_from_debug(d)}")
            print()
        except Exception as e:
            print(f"=== {label} ERROR: {e} ===\n")


if __name__ == "__main__":
    main()
