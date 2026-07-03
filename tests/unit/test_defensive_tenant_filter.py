"""PR-F1-05 — Defensive tenant filter dedicated (TD-08)."""
from __future__ import annotations

from typing import Set
from unittest.mock import patch
from uuid import UUID

import pytest
from sqlalchemy import Select, select
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, Grouping

from app.core.exceptions import SecurityError
from app.core.tenant.context import reset_tenant_context, set_tenant_context
from app.core.tenant.context import TenantContext
from app.infrastructure.database.query_helpers import (
    DEFENSIVE_TENANT_FILTER_REQUIRED,
    apply_tenant_filter,
    apply_tenant_filter_to_text_clause,
)
from app.infrastructure.database.tables import UsuarioTable
from sqlalchemy import text
from tests.integration.helpers.hybrid_mock_metadata import (
    build_dedicated_metadata,
    build_shared_metadata,
    build_tenant_context,
)

SHARED_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
DEDICATED_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")


def _client_ids_in_where(whereclause) -> Set[UUID]:
    ids: Set[UUID] = set()
    if whereclause is None:
        return ids
    if isinstance(whereclause, BooleanClauseList):
        for clause in whereclause.clauses:
            ids |= _client_ids_in_where(clause)
    elif isinstance(whereclause, Grouping):
        ids |= _client_ids_in_where(whereclause.element)
    elif isinstance(whereclause, BinaryExpression):
        left_key = getattr(whereclause.left, "key", None)
        right_key = getattr(whereclause.right, "key", None)
        if left_key == "cliente_id":
            value = getattr(whereclause.right, "value", None)
            if isinstance(value, UUID):
                ids.add(value)
        if right_key == "cliente_id":
            value = getattr(whereclause.left, "value", None)
            if isinstance(value, UUID):
                ids.add(value)
    return ids


@pytest.fixture
def dedicated_tenant_context():
    ctx = build_tenant_context(
        DEDICATED_ID,
        build_dedicated_metadata(DEDICATED_ID),
        subdominio="dedicated-mock",
        codigo_cliente="DEDICATED",
    )
    tokens = set_tenant_context(ctx)
    yield ctx
    reset_tenant_context(tokens)


@pytest.fixture
def shared_tenant_context():
    ctx = build_tenant_context(
        SHARED_ID,
        build_shared_metadata(SHARED_ID),
        subdominio="shared-mock",
        codigo_cliente="SHARED",
    )
    tokens = set_tenant_context(ctx)
    yield ctx
    reset_tenant_context(tokens)


@pytest.mark.unit
def test_dedicated_mock_applies_defensive_filter(dedicated_tenant_context):
    query = select(UsuarioTable).where(UsuarioTable.c.es_activo.is_(True))
    filtered = apply_tenant_filter(query, table_name="usuario")
    assert DEDICATED_ID in _client_ids_in_where(filtered.whereclause)


@pytest.mark.unit
def test_shared_path_still_applies_filter(shared_tenant_context):
    query = select(UsuarioTable)
    filtered = apply_tenant_filter(query, table_name="usuario")
    assert SHARED_ID in _client_ids_in_where(filtered.whereclause)


@pytest.mark.unit
def test_dedicated_text_clause_applies_defensive_filter(dedicated_tenant_context):
    query = text("SELECT * FROM usuario WHERE es_activo = 1")
    filtered = apply_tenant_filter_to_text_clause(query, table_name="usuario")
    assert "cliente_id" in filtered.text.lower()


@pytest.mark.unit
def test_dedicated_fails_when_filter_cannot_be_injected(dedicated_tenant_context):
    query = text("SELECT * FROM usuario WHERE es_activo = 1")
    with patch(
        "app.infrastructure.database.query_helpers._add_tenant_filter_to_sql",
        return_value="SELECT * FROM usuario WHERE es_activo = 1",
    ):
        with pytest.raises(SecurityError) as exc:
            apply_tenant_filter_to_text_clause(query, table_name="usuario")
    assert exc.value.internal_code == DEFENSIVE_TENANT_FILTER_REQUIRED


@pytest.mark.unit
def test_shared_text_clause_keeps_soft_fallback_on_injection_failure(shared_tenant_context):
    query = text("SELECT * FROM usuario WHERE es_activo = 1")
    with patch(
        "app.infrastructure.database.query_helpers._add_tenant_filter_to_sql",
        side_effect=RuntimeError("parse error"),
    ):
        result = apply_tenant_filter_to_text_clause(query, table_name="usuario")
    assert result.text == query.text


@pytest.mark.unit
def test_is_dedicated_detects_database_type_multi():
    ctx = TenantContext(
        client_id=DEDICATED_ID,
        database_type="multi",
        tipo_instalacion="dedicated",
    )
    tokens = set_tenant_context(ctx)
    try:
        query = select(UsuarioTable)
        filtered = apply_tenant_filter(query, table_name="usuario")
        assert DEDICATED_ID in _client_ids_in_where(filtered.whereclause)
    finally:
        reset_tenant_context(tokens)
