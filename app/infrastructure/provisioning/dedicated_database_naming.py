"""Política de nombres BD/login Dedicated — BL-F4 §11 S2/S3."""
from __future__ import annotations

import re
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import ValidationError

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_]{1,128}$")
_CODIGO_NORMALIZE_RE = re.compile(r"[^A-Za-z0-9]+")


def normalize_codigo_cliente(codigo_cliente: str) -> str:
    cleaned = _CODIGO_NORMALIZE_RE.sub("_", (codigo_cliente or "").strip()).strip("_")
    if not cleaned:
        raise ValidationError(
            detail="codigo_cliente inválido para naming de BD dedicated.",
            internal_code="INVALID_DEDICATED_CODIGO",
        )
    return cleaned.upper()


def build_dedicated_database_name(codigo_cliente: str, *, cliente_id: UUID | None = None) -> str:
    """
    Política v1: ``{prefix}{codigo_normalizado}`` en minúsculas.

    ``cliente_id`` reservado para evolución de colisiones (no usado en v1).
    """
    _ = cliente_id
    prefix = settings.PROVISIONING_DEDICATED_DB_NAME_PREFIX
    normalized = normalize_codigo_cliente(codigo_cliente).lower()
    name = f"{prefix}{normalized}"
    max_len = settings.PROVISIONING_DEDICATED_DB_NAME_MAX_LENGTH
    if len(name) > max_len:
        name = name[:max_len]
    assert_sql_identifier(name, field="database_name")
    return name


def build_dedicated_app_login_name(codigo_cliente: str, *, cliente_id: UUID | None = None) -> str:
    _ = cliente_id
    prefix = settings.PROVISIONING_DEDICATED_LOGIN_PREFIX
    normalized = normalize_codigo_cliente(codigo_cliente).lower()
    name = f"{prefix}{normalized}"
    max_len = settings.PROVISIONING_DEDICATED_LOGIN_MAX_LENGTH
    if len(name) > max_len:
        name = name[:max_len]
    assert_sql_identifier(name, field="app_login_name")
    return name


def assert_sql_identifier(value: str, *, field: str) -> None:
    if not _IDENTIFIER_RE.match(value):
        raise ValidationError(
            detail=f"{field} contiene caracteres no permitidos para SQL Server.",
            internal_code="INVALID_SQL_IDENTIFIER",
        )


def quote_sql_identifier(identifier: str) -> str:
    assert_sql_identifier(identifier, field="identifier")
    return f"[{identifier.replace(']', ']]')}]"


def escape_sql_literal(value: str) -> str:
    return value.replace("'", "''")


__all__ = [
    "assert_sql_identifier",
    "build_dedicated_app_login_name",
    "build_dedicated_database_name",
    "escape_sql_literal",
    "normalize_codigo_cliente",
    "quote_sql_identifier",
]
