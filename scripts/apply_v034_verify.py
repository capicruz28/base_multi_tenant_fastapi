"""Apply V034 and verify session FK state (dev/Docker helper)."""
from __future__ import annotations

from pathlib import Path

import pyodbc

from app.core.config import settings

SQL_PATH = Path(__file__).resolve().parents[1] / "app/bootstrap_v2/01_schema/V034__remove_cross_plane_session_empresa_fks.sql"


def _split_batches(raw: str) -> list[str]:
    batches: list[str] = []
    current: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip().upper()
        if stripped == "GO" or stripped == "GO;":
            if current:
                batches.append("\n".join(current))
                current = []
            continue
        current.append(line)
    if current:
        batches.append("\n".join(current))
    return batches


def _executable_batch(batch: str) -> str:
    lines = [
        line
        for line in batch.splitlines()
        if line.strip() and not line.strip().startswith("--")
    ]
    return "\n".join(lines)


def apply_v034() -> None:
    raw = SQL_PATH.read_text(encoding="utf-8")
    conn = pyodbc.connect(settings.get_database_url(is_admin=True), autocommit=True)
    cur = conn.cursor()
    for batch in _split_batches(raw):
        sql = _executable_batch(batch)
        if not sql:
            continue
        cur.execute(sql)
        if cur.description:
            for row in cur.fetchall():
                print(row[0] if len(row) == 1 else row)
        while cur.nextset():
            if cur.description:
                for row in cur.fetchall():
                    print(row[0] if len(row) == 1 else row)
    conn.close()


def verify_fks() -> None:
    conn = pyodbc.connect(settings.get_database_url(is_admin=True))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT tp.name, fk.name, tr.name
        FROM sys.foreign_keys fk
        JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
        JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
        WHERE tp.name IN ('user_session','token_family','refresh_tokens')
        ORDER BY tp.name, fk.name
        """
    )
    rows = cur.fetchall()
    conn.close()
    print("Session store FKs:")
    for row in rows:
        print(f"  {row[0]}.{row[1]} -> {row[2]}")
    cross = [r for r in rows if r[2] in ("usuario", "org_empresa")]
    if cross:
        raise SystemExit(f"Cross-plane FKs remain: {cross}")
    print("OK: no cross-plane FKs")


if __name__ == "__main__":
    apply_v034()
    verify_fks()
