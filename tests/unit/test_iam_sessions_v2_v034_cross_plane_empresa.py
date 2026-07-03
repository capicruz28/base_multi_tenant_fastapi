"""V034 — Session Store cross-plane FK policy (empresa_id lógico)."""
from __future__ import annotations

import os

import pytest

from app.infrastructure.database.tables import (
    RefreshTokensTable,
    TokenFamilyTable,
    UserSessionTable,
)

SESSION_STORE_TABLES = (
    UserSessionTable,
    TokenFamilyTable,
    RefreshTokensTable,
)

CROSS_PLANE_LOGICAL_COLUMNS = frozenset({"usuario_id", "empresa_id"})


@pytest.mark.unit
def test_v034_orm_session_tables_have_no_fk_to_org_empresa():
    for table in SESSION_STORE_TABLES:
        for col in table.c:
            for fk in col.foreign_keys:
                assert fk.column.table.name != "org_empresa", (
                    f"{table.name}.{col.name} must not FK to org_empresa"
                )


@pytest.mark.unit
def test_v034_logical_columns_present_without_fk():
    assert "empresa_id" in UserSessionTable.c
    assert "empresa_id" in RefreshTokensTable.c
    assert "usuario_id" in TokenFamilyTable.c

    for table in SESSION_STORE_TABLES:
        for col_name in CROSS_PLANE_LOGICAL_COLUMNS:
            if col_name not in table.c:
                continue
            assert not any(
                fk.parent.name == col_name for fk in table.foreign_keys
            ), f"{table.name}.{col_name} must remain FK-free"


@pytest.mark.integration
def test_v034_database_has_no_session_fk_to_org_empresa():
    if os.getenv("SKIP_DB_INTEGRATION_TESTS", "").lower() in {"1", "true", "yes"}:
        pytest.skip("SKIP_DB_INTEGRATION_TESTS activo")

    try:
        import pyodbc
        from app.core.config import settings
    except ImportError:
        pytest.skip("pyodbc no disponible")

    if not settings.DB_ADMIN_SERVER or not settings.DB_ADMIN_DATABASE:
        pytest.skip("Credenciales BD admin no configuradas")

    conn = pyodbc.connect(settings.get_database_url(is_admin=True))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT tp.name AS parent_table, fk.name AS fk_name, tr.name AS ref_table
        FROM sys.foreign_keys fk
        INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
        INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
        WHERE tp.name IN ('user_session', 'token_family', 'refresh_tokens')
          AND tr.name IN ('usuario', 'org_empresa')
        """
    )
    rows = cur.fetchall()
    conn.close()
    assert rows == [], f"Cross-plane session FKs still present: {rows}"


@pytest.mark.integration
def test_v034_database_intra_cp_session_fks_preserved():
    if os.getenv("SKIP_DB_INTEGRATION_TESTS", "").lower() in {"1", "true", "yes"}:
        pytest.skip("SKIP_DB_INTEGRATION_TESTS activo")

    try:
        import pyodbc
        from app.core.config import settings
    except ImportError:
        pytest.skip("pyodbc no disponible")

    if not settings.DB_ADMIN_SERVER or not settings.DB_ADMIN_DATABASE:
        pytest.skip("Credenciales BD admin no configuradas")

    expected = {
        "FK_session_cliente",
        "FK_family_session",
        "FK_family_cliente",
        "FK_token_family",
        "FK_token_session",
        "FK_token_parent",
        "FK_token_cliente",
    }
    conn = pyodbc.connect(settings.get_database_url(is_admin=True))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT fk.name
        FROM sys.foreign_keys fk
        INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
        WHERE tp.name IN ('user_session', 'token_family', 'refresh_tokens')
        """
    )
    present = {row[0] for row in cur.fetchall()}
    conn.close()
    missing = expected - present
    assert not missing, f"Missing intra-CP session FKs after V034: {sorted(missing)}"
