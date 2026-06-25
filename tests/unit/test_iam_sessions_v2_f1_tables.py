"""F1 — validación ORM tablas IAM Session Management V3 vs DDL y BD dev."""
from __future__ import annotations

import os
from typing import AbstractSet

import pytest

from app.infrastructure.database.tables import (
    RefreshTokensTable,
    TokenFamilyTable,
    UserSessionTable,
)

USER_SESSION_COLUMNS: AbstractSet[str] = {
    "session_id",
    "usuario_id",
    "cliente_id",
    "empresa_id",
    "login_method",
    "selection_token_completed",
    "platform",
    "device_name",
    "device_id",
    "device_fingerprint",
    "user_agent",
    "login_ip",
    "last_seen_ip",
    "is_active",
    "revoked_at",
    "revoked_reason",
    "last_refresh_at",
    "last_business_activity_at",
    "created_at",
    "expires_at",
}

TOKEN_FAMILY_COLUMNS: AbstractSet[str] = {
    "family_id",
    "session_id",
    "usuario_id",
    "cliente_id",
    "current_token_id",
    "is_compromised",
    "compromised_at",
    "invalidation_reason",
    "created_at",
}

REFRESH_TOKENS_V3_COLUMNS: AbstractSet[str] = {
    "token_id",
    "family_id",
    "session_id",
    "parent_token_id",
    "cliente_id",
    "empresa_id",
    "usuario_id",
    "token_hash",
    "expires_at",
    "created_at",
    "last_used_at",
    "is_used",
    "used_at",
    "is_revoked",
    "revoked_at",
    "revoked_reason",
}

REFRESH_TOKENS_LEGACY_COLUMNS: AbstractSet[str] = {
    "client_type",
    "device_name",
    "device_id",
    "ip_address",
    "user_agent",
    "uso_count",
}

USER_SESSION_INDEXES = {
    "IDX_session_usuario_activo",
    "IDX_session_cliente",
    "IDX_session_device_usuario",
    "IDX_session_expires",
    "IDX_session_empresa",
    "IDX_session_login_method",
    "IDX_session_last_seen_ip",
    "IDX_session_business_activity",
}

TOKEN_FAMILY_INDEXES = {
    "IDX_family_session",
    "IDX_family_comprometida",
    "IDX_family_usuario",
    "IDX_family_cliente",
    "IDX_family_current_token",
}

REFRESH_TOKENS_INDEXES = {
    "IDX_token_hash_activo",
    "IDX_token_family_estado",
    "IDX_token_session_activo",
    "IDX_token_parent",
    "IDX_token_usuario_cliente",
    "IDX_token_cleanup",
    "IDX_token_used_activo",
}


def _column_names(table) -> set[str]:
    return {column.name for column in table.c}


def _index_names(table) -> set[str]:
    return {index.name for index in table.indexes}


def _check_constraint_names(table) -> set[str]:
    return {constraint.name for constraint in table.constraints if constraint.name and constraint.name.startswith("CK_")}


@pytest.mark.unit
def test_f1_user_session_table_columns_match_ddl():
    assert _column_names(UserSessionTable) == USER_SESSION_COLUMNS


@pytest.mark.unit
def test_f1_token_family_table_columns_match_ddl():
    assert _column_names(TokenFamilyTable) == TOKEN_FAMILY_COLUMNS


@pytest.mark.unit
def test_f1_refresh_tokens_table_columns_match_ddl_v3():
    assert _column_names(RefreshTokensTable) == REFRESH_TOKENS_V3_COLUMNS


@pytest.mark.unit
def test_f1_refresh_tokens_table_has_no_legacy_v1_columns():
    assert not _column_names(RefreshTokensTable) & REFRESH_TOKENS_LEGACY_COLUMNS


@pytest.mark.unit
def test_f1_user_session_check_constraints():
    assert _check_constraint_names(UserSessionTable) == {
        "CK_session_login_method",
        "CK_session_platform",
        "CK_session_revoked_reason",
    }


@pytest.mark.unit
def test_f1_token_family_check_constraints():
    assert _check_constraint_names(TokenFamilyTable) == {"CK_family_invalidation_reason"}


@pytest.mark.unit
def test_f1_refresh_tokens_check_constraints_and_unique():
    assert _check_constraint_names(RefreshTokensTable) == {"CK_token_revoked_reason"}
    unique_names = {
        constraint.name
        for constraint in RefreshTokensTable.constraints
        if constraint.name and constraint.name.startswith("UQ_")
    }
    assert unique_names == {"UQ_token_hash"}


@pytest.mark.unit
def test_f1_user_session_indexes_match_ddl():
    assert _index_names(UserSessionTable) == USER_SESSION_INDEXES


@pytest.mark.unit
def test_f1_token_family_indexes_match_ddl():
    assert _index_names(TokenFamilyTable) == TOKEN_FAMILY_INDEXES


@pytest.mark.unit
def test_f1_refresh_tokens_indexes_match_ddl():
    assert _index_names(RefreshTokensTable) == REFRESH_TOKENS_INDEXES


@pytest.mark.unit
def test_f1_foreign_keys_defined():
    user_session_fks = {fk.parent.name for fk in UserSessionTable.foreign_keys}
    assert user_session_fks == {"usuario_id", "cliente_id", "empresa_id"}

    token_family_fks = {fk.parent.name for fk in TokenFamilyTable.foreign_keys}
    assert token_family_fks == {"session_id", "usuario_id", "cliente_id"}

    refresh_fks = {fk.parent.name for fk in RefreshTokensTable.foreign_keys}
    assert refresh_fks == {
        "family_id",
        "session_id",
        "parent_token_id",
        "cliente_id",
        "empresa_id",
        "usuario_id",
    }


@pytest.mark.unit
def test_f1_token_family_current_token_id_has_no_fk():
    current_token_fks = [
        fk
        for fk in TokenFamilyTable.foreign_keys
        if fk.parent.name == "current_token_id"
    ]
    assert current_token_fks == []


@pytest.mark.unit
def test_f1_tables_exported_from_tables_module():
    from app.infrastructure.database import tables as tables_module

    assert "UserSessionTable" in tables_module.__all__
    assert "TokenFamilyTable" in tables_module.__all__
    assert "RefreshTokensTable" in tables_module.__all__


@pytest.mark.integration
def test_f1_orm_columns_match_database_schema():
    if os.getenv("SKIP_DB_INTEGRATION_TESTS", "").lower() in {"1", "true", "yes"}:
        pytest.skip("SKIP_DB_INTEGRATION_TESTS activo")

    try:
        import pyodbc
        from app.core.config import settings
    except ImportError:
        pytest.skip("pyodbc no disponible")

    if not settings.DB_SERVER or not settings.DB_DATABASE:
        pytest.skip("Credenciales BD no configuradas")

    expected_by_table = {
        "user_session": USER_SESSION_COLUMNS,
        "token_family": TOKEN_FAMILY_COLUMNS,
        "refresh_tokens": REFRESH_TOKENS_V3_COLUMNS,
    }
    orm_by_table = {
        "user_session": UserSessionTable,
        "token_family": TokenFamilyTable,
        "refresh_tokens": RefreshTokensTable,
    }

    conn = pyodbc.connect(settings.get_database_url(is_admin=False))
    cur = conn.cursor()
    gaps: list[str] = []

    for table_name, expected_cols in expected_by_table.items():
        cur.execute(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?",
            table_name,
        )
        db_cols = {row[0].lower() for row in cur.fetchall()}
        orm_cols = _column_names(orm_by_table[table_name])
        if db_cols != expected_cols:
            gaps.append(f"db:{table_name}:unexpected={sorted(db_cols ^ expected_cols)}")
        if orm_cols != db_cols:
            gaps.append(f"orm:{table_name}:mismatch={sorted(orm_cols ^ db_cols)}")

    conn.close()
    assert not gaps, f"Desalineación ORM/BD: {gaps}"
