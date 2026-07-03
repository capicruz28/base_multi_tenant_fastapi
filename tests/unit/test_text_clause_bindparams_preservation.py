"""RC-02A-FIX — Preservación de bindparams al reescribir TextClause (TD-08)."""
from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import InvalidRequestError

from app.infrastructure.database.query_helpers import (
    _extract_text_clause_bind_params,
    apply_tenant_filter_to_text_clause,
)
from tests.integration.helpers.hybrid_mock_metadata import (
    build_dedicated_metadata,
    build_tenant_context,
)
from app.core.tenant.context import reset_tenant_context, set_tenant_context

DEDICATED_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")


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


def _assert_all_params_bound(clause) -> dict:
    """compile() raises InvalidRequestError if any bind param lacks a value."""
    compiled = clause.compile()
    return dict(compiled.params)


@pytest.mark.unit
def test_extract_text_clause_bind_params_sa2_update():
    empresa_id = uuid4()
    usuario_id = uuid4()
    query = text(
        """
        UPDATE usuario
        SET empresa_default_id = :empresa_id
        WHERE usuario_id = :usuario_id
          AND es_eliminado = 0
        """
    ).bindparams(empresa_id=empresa_id, usuario_id=usuario_id)

    extracted = _extract_text_clause_bind_params(query)
    assert extracted == {"empresa_id": empresa_id, "usuario_id": usuario_id}


@pytest.mark.unit
def test_update_preserves_multiple_bindparams(dedicated_tenant_context):
    empresa_id = uuid4()
    usuario_id = uuid4()
    query = text(
        """
        UPDATE usuario
        SET empresa_default_id = :empresa_id
        WHERE usuario_id = :usuario_id
          AND es_eliminado = 0
        """
    ).bindparams(empresa_id=empresa_id, usuario_id=usuario_id)

    filtered = apply_tenant_filter_to_text_clause(
        query,
        table_name="usuario",
    )
    params = _assert_all_params_bound(filtered)

    assert params["empresa_id"] == empresa_id
    assert params["usuario_id"] == usuario_id
    assert params["cliente_id"] == DEDICATED_ID
    assert "cliente_id" in filtered.text.lower()


@pytest.mark.unit
def test_delete_preserves_bindparams(dedicated_tenant_context):
    row_id = uuid4()
    query = text(
        "DELETE FROM documento WHERE documento_id = :documento_id AND es_eliminado = 0"
    ).bindparams(documento_id=row_id)

    filtered = apply_tenant_filter_to_text_clause(query, table_name="documento")
    params = _assert_all_params_bound(filtered)

    assert params["documento_id"] == row_id
    assert params["cliente_id"] == DEDICATED_ID


@pytest.mark.unit
def test_select_preserves_bindparams(dedicated_tenant_context):
    usuario_id = uuid4()
    query = text(
        "SELECT * FROM usuario WHERE usuario_id = :usuario_id AND es_activo = 1"
    ).bindparams(usuario_id=usuario_id)

    filtered = apply_tenant_filter_to_text_clause(query, table_name="usuario")
    params = _assert_all_params_bound(filtered)

    assert params["usuario_id"] == usuario_id
    assert params["cliente_id"] == DEDICATED_ID


@pytest.mark.unit
def test_preserves_uuid_bindparams(dedicated_tenant_context):
    ids = {name: uuid4() for name in ("a_id", "b_id", "c_id")}
    query = text(
        "UPDATE t SET x = :a_id WHERE y = :b_id AND z = :c_id"
    ).bindparams(**ids)

    filtered = apply_tenant_filter_to_text_clause(query, table_name="t")
    params = _assert_all_params_bound(filtered)

    for name, value in ids.items():
        assert params[name] == value
        assert isinstance(params[name], UUID)


@pytest.mark.unit
def test_preserves_none_bindparams(dedicated_tenant_context):
    usuario_id = uuid4()
    query = text(
        """
        UPDATE usuario
        SET empresa_default_id = NULL
        WHERE usuario_id = :usuario_id
          AND empresa_default_id = :empresa_id
        """
    ).bindparams(usuario_id=usuario_id, empresa_id=None)

    filtered = apply_tenant_filter_to_text_clause(query, table_name="usuario")
    params = _assert_all_params_bound(filtered)

    assert params["usuario_id"] == usuario_id
    assert params["empresa_id"] is None
    assert params["cliente_id"] == DEDICATED_ID


@pytest.mark.unit
def test_empresa_preference_update_pattern_no_invalid_request(dedicated_tenant_context):
    """Regresión RC-02A: UPDATE empresa_default_id en dedicated sin perder bindparams."""
    empresa_id = uuid4()
    usuario_id = uuid4()
    query = text(
        """
        UPDATE usuario
        SET empresa_default_id = :empresa_id
        WHERE usuario_id = :usuario_id
          AND es_eliminado = 0
        """
    ).bindparams(empresa_id=empresa_id, usuario_id=usuario_id)

    filtered = apply_tenant_filter_to_text_clause(query, table_name="usuario")

    try:
        params = filtered.compile().params
    except InvalidRequestError as exc:
        pytest.fail(f"bindparams perdidos: {exc}")

    assert params["empresa_id"] == empresa_id
    assert params["usuario_id"] == usuario_id
    assert params["cliente_id"] == DEDICATED_ID
