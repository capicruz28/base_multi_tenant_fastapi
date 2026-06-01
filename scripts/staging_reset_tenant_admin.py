#!/usr/bin/env python3
"""
Reset controlado de contraseña del admin tenant (staging / QA).

No altera RBAC ni módulos. Solo actualiza hash bcrypt en `usuario`.

Uso:
  python scripts/staging_reset_tenant_admin.py --subdominio prueba --password admin123
  python scripts/staging_reset_tenant_admin.py --cliente-id <UUID> --username admin --password admin123

Contraseña por defecto en staging: admin123 (mismo hash que seeds QA D010).
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from app.core.security.password import get_password_hash
from app.infrastructure.database.connection_async import DatabaseConnection, get_db_connection

DEFAULT_ADMIN = "admin"
DEFAULT_PASSWORD = "admin123"


async def _resolve_cliente_id(
    session, *, subdominio: str | None, cliente_id: UUID | None
) -> UUID:
    if cliente_id is not None:
        return cliente_id
    if not subdominio:
        raise ValueError("Indique --subdominio o --cliente-id")
    row = (
        await session.execute(
            text(
                "SELECT cliente_id FROM cliente WHERE subdominio = :sub AND es_activo = 1"
            ),
            {"sub": subdominio},
        )
    ).first()
    if not row:
        raise ValueError(f"Cliente no encontrado para subdominio={subdominio!r}")
    return UUID(str(row[0]))


async def reset_admin_password(
    *,
    subdominio: str | None,
    cliente_id: UUID | None,
    username: str,
    password: str,
    dry_run: bool,
) -> dict:
    pwd_hash = get_password_hash(password)
    async with get_db_connection(DatabaseConnection.ADMIN) as session:
        cid = await _resolve_cliente_id(
            session, subdominio=subdominio, cliente_id=cliente_id
        )
        check = (
            await session.execute(
                text(
                    """
                    SELECT usuario_id, nombre_usuario, correo
                    FROM usuario
                    WHERE cliente_id = :cid AND nombre_usuario = :user AND es_eliminado = 0
                    """
                ),
                {"cid": str(cid), "user": username},
            )
        ).first()
        if not check:
            raise ValueError(
                f"Usuario {username!r} no encontrado en cliente_id={cid}"
            )

        if dry_run:
            return {
                "dry_run": True,
                "cliente_id": str(cid),
                "usuario_id": str(check[0]),
                "nombre_usuario": check[1],
                "correo": check[2],
                "password_reset": False,
            }

        result = await session.execute(
            text(
                """
                UPDATE usuario
                SET contrasena = :hash, requiere_cambio_contrasena = 0
                WHERE cliente_id = :cid AND nombre_usuario = :user AND es_eliminado = 0
                """
            ),
            {"hash": pwd_hash, "cid": str(cid), "user": username},
        )
        await session.commit()
        return {
            "dry_run": False,
            "cliente_id": str(cid),
            "usuario_id": str(check[0]),
            "nombre_usuario": check[1],
            "rows_updated": result.rowcount,
            "password_reset": True,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset admin tenant (staging)")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--subdominio")
    g.add_argument("--cliente-id")
    parser.add_argument("--username", default=DEFAULT_ADMIN)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cliente_id = UUID(args.cliente_id) if args.cliente_id else None
    try:
        import json

        out = asyncio.run(
            reset_admin_password(
                subdominio=args.subdominio,
                cliente_id=cliente_id,
                username=args.username,
                password=args.password,
                dry_run=args.dry_run,
            )
        )
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
