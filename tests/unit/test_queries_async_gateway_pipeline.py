"""PR-F1-06 — queries_async gateway pipeline alignment (RD-06)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from sqlalchemy import select, text

from app.core.exceptions import ValidationError
from app.core.tenant.context import reset_tenant_context, set_tenant_context
from app.core.tenant.routing import (
    OPERATION_CLASS_CONTROL_PLANE,
    OPERATION_CLASS_TENANT_DATA,
)
from app.infrastructure.database.connection_async import DatabaseConnection
from app.infrastructure.database.queries_async import (
    _coerce_client_id_uuid,
    _get_connection_context,
    _operation_class_for,
    _prepare_core_query_for_gateway,
    _prepare_text_clause_for_gateway,
    _resolve_effective_client_id,
)
from app.infrastructure.database.tables import UsuarioTable
from tests.integration.helpers.hybrid_mock_metadata import (
    build_shared_metadata,
    build_tenant_context,
)

CLIENT_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")


@pytest.mark.unit
def test_operation_class_for_maps_connection_types():
    assert _operation_class_for(DatabaseConnection.ADMIN) == OPERATION_CLASS_CONTROL_PLANE
    assert _operation_class_for(DatabaseConnection.DEFAULT) == OPERATION_CLASS_TENANT_DATA


@pytest.mark.unit
def test_coerce_client_id_uuid_accepts_uuid_and_int():
    assert _coerce_client_id_uuid(CLIENT_ID) == CLIENT_ID
    assert _coerce_client_id_uuid(42) == UUID(int=42)


@pytest.mark.unit
def test_resolve_effective_client_id_prefers_explicit_param():
    ctx = build_tenant_context(
        CLIENT_ID,
        build_shared_metadata(CLIENT_ID),
        subdominio="shared",
        codigo_cliente="SHARED",
    )
    tokens = set_tenant_context(ctx)
    try:
        other = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        assert _resolve_effective_client_id(other) == other
    finally:
        reset_tenant_context(tokens)


@pytest.mark.unit
def test_get_connection_context_admin_uses_control_plane_path():
    with patch(
        "app.infrastructure.database.queries_async.get_db_connection",
        return_value=MagicMock(),
    ) as mock_conn:
        _get_connection_context(DatabaseConnection.ADMIN)
    mock_conn.assert_called_once_with(DatabaseConnection.ADMIN)


@pytest.mark.unit
def test_get_connection_context_default_uses_tenant_gateway_path():
    with patch(
        "app.infrastructure.database.queries_async.get_connection_for_tenant",
        return_value=MagicMock(),
    ) as mock_tenant:
        _get_connection_context(DatabaseConnection.DEFAULT, client_id=CLIENT_ID)
    mock_tenant.assert_called_once_with(
        cliente_id=CLIENT_ID,
        operation_class=OPERATION_CLASS_TENANT_DATA,
    )


@pytest.mark.unit
def test_prepare_core_query_applies_tenant_filter():
    ctx = build_tenant_context(
        CLIENT_ID,
        build_shared_metadata(CLIENT_ID),
        subdominio="shared",
        codigo_cliente="SHARED",
    )
    tokens = set_tenant_context(ctx)
    try:
        query = select(UsuarioTable)
        prepared = _prepare_core_query_for_gateway(
            query,
            client_id=None,
            skip_tenant_validation=False,
        )
        assert prepared.whereclause is not None
    finally:
        reset_tenant_context(tokens)


@pytest.mark.unit
def test_prepare_text_clause_applies_cliente_id_filter():
    ctx = build_tenant_context(
        CLIENT_ID,
        build_shared_metadata(CLIENT_ID),
        subdominio="shared",
        codigo_cliente="SHARED",
    )
    tokens = set_tenant_context(ctx)
    try:
        query = text("SELECT * FROM usuario WHERE es_activo = 1")
        prepared = _prepare_text_clause_for_gateway(
            query,
            client_id=None,
            table_name="usuario",
            skip_tenant_validation=False,
        )
        assert "cliente_id" in prepared.text.lower()
    finally:
        reset_tenant_context(tokens)


@pytest.mark.unit
def test_assert_skip_tenant_validation_raises_when_bypass_disabled():
    from app.infrastructure.database import queries_async

    with patch.object(queries_async.settings, "ALLOW_TENANT_FILTER_BYPASS", False):
        with pytest.raises(ValidationError) as exc:
            queries_async._assert_skip_tenant_validation_allowed(True)
    assert exc.value.internal_code == "TENANT_VALIDATION_BYPASS_DISABLED"
