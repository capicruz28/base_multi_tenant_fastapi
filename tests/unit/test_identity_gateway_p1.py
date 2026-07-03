"""F6-P1 — Identity Gateway Core (login únicamente)."""
from __future__ import annotations

from typing import Set
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from sqlalchemy import select

from app.core.identity.identity_context import IdentityContext
from app.core.identity.identity_gateway import IdentityGateway
from app.core.identity.identity_scope import IdentityScope
from app.core.tenant.context import reset_tenant_context, set_tenant_context
from app.infrastructure.database.query_helpers import apply_tenant_filter
from app.infrastructure.database.tables import UsuarioTable
from tests.integration.helpers.hybrid_mock_metadata import (
    build_dedicated_metadata,
    build_shared_metadata,
    build_tenant_context,
)

SHARED_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
DEDICATED_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
USER_ID = UUID("11111111-1111-4111-8111-111111111111")


def _client_ids_in_where(whereclause) -> Set[UUID]:
    ids: Set[UUID] = set()
    if whereclause is None:
        return ids
    from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, Grouping

    if isinstance(whereclause, BooleanClauseList):
        for clause in whereclause.clauses:
            ids |= _client_ids_in_where(clause)
    elif isinstance(whereclause, Grouping):
        ids |= _client_ids_in_where(whereclause.element)
    elif isinstance(whereclause, BinaryExpression):
        left_key = getattr(whereclause.left, "key", None)
        if left_key == "cliente_id":
            value = getattr(whereclause.right, "value", None)
            if isinstance(value, UUID):
                ids.add(value)
    return ids


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


@pytest.mark.unit
def test_resolve_identity_scope_shared_returns_row_scoped(shared_tenant_context):
    assert IdentityGateway.resolve_identity_scope() == IdentityScope.ROW_SCOPED


@pytest.mark.unit
def test_resolve_identity_scope_dedicated_returns_engine_scoped(dedicated_tenant_context):
    assert IdentityGateway.resolve_identity_scope() == IdentityScope.ENGINE_SCOPED


@pytest.mark.unit
def test_engine_scoped_skips_tenant_filter(dedicated_tenant_context):
    query = select(UsuarioTable).where(UsuarioTable.c.nombre_usuario == "alice")
    filtered = apply_tenant_filter(
        query,
        client_id=DEDICATED_ID,
        table_name="usuario",
        identity_scope=IdentityScope.ENGINE_SCOPED,
    )
    assert _client_ids_in_where(filtered.whereclause) == set()


@pytest.mark.unit
def test_row_scoped_still_applies_filter(shared_tenant_context):
    query = select(UsuarioTable).where(UsuarioTable.c.nombre_usuario == "alice")
    filtered = apply_tenant_filter(
        query,
        client_id=SHARED_ID,
        table_name="usuario",
        identity_scope=IdentityScope.ROW_SCOPED,
    )
    assert SHARED_ID in _client_ids_in_where(filtered.whereclause)


@pytest.mark.unit
def test_normalize_user_cliente_id_dedicated_null_uses_context(dedicated_tenant_context):
    user = {"cliente_id": None, "usuario_id": USER_ID}
    ctx = IdentityContext(cliente_id=DEDICATED_ID)
    normalized = IdentityGateway.normalize_user_cliente_id(user, ctx)
    assert normalized["cliente_id"] == DEDICATED_ID


@pytest.mark.unit
def test_normalize_user_cliente_id_shared_unchanged(shared_tenant_context):
    user = {"cliente_id": SHARED_ID, "usuario_id": USER_ID}
    ctx = IdentityContext(cliente_id=SHARED_ID)
    normalized = IdentityGateway.normalize_user_cliente_id(user, ctx)
    assert normalized["cliente_id"] == SHARED_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_by_username_dedicated_uses_engine_scoped_executor(
    dedicated_tenant_context,
):
    ctx = IdentityContext(cliente_id=DEDICATED_ID)
    mock_user = {"usuario_id": USER_ID, "nombre_usuario": "alice"}

    with patch(
        "app.core.identity.identity_gateway.execute_identity_query",
        new_callable=AsyncMock,
    ) as mock_exec:
        mock_exec.return_value = [mock_user]
        result = await IdentityGateway.get_user_by_username(ctx, "alice")

    assert result == mock_user
    mock_exec.assert_awaited_once()
    assert mock_exec.call_args.kwargs["identity_scope"] == IdentityScope.ENGINE_SCOPED
    assert mock_exec.call_args.kwargs["cliente_id"] == DEDICATED_ID


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_by_username_shared_uses_row_scoped_executor(
    shared_tenant_context,
):
    ctx = IdentityContext(cliente_id=SHARED_ID)
    mock_user = {"usuario_id": USER_ID, "nombre_usuario": "bob"}

    with patch(
        "app.core.identity.identity_gateway.execute_identity_query",
        new_callable=AsyncMock,
    ) as mock_exec:
        mock_exec.return_value = [mock_user]
        result = await IdentityGateway.get_user_by_username(ctx, "bob")

    assert result == mock_user
    mock_exec.assert_awaited_once()
    assert mock_exec.call_args.kwargs["identity_scope"] == IdentityScope.ROW_SCOPED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_authenticate_user_delegates_lookup_to_identity_gateway():
    from app.modules.auth.application.services.auth_service import AuthService

    cliente_id = SHARED_ID
    mock_user = {
        "usuario_id": USER_ID,
        "cliente_id": cliente_id,
        "nombre_usuario": "bob",
        "contrasena": "hashed",
        "es_activo": True,
    }

    with (
        patch(
            "app.core.identity.identity_gateway.IdentityGateway.get_user_by_username",
            new_callable=AsyncMock,
            return_value=mock_user,
        ) as mock_lookup,
        patch(
            "app.core.identity.identity_gateway.IdentityGateway.normalize_user_cliente_id",
            side_effect=lambda u, _ctx: u,
        ),
        patch(
            "app.core.identity.identity_gateway.IdentityGateway.update_last_access",
            new_callable=AsyncMock,
        ),
        patch(
            "app.modules.auth.application.services.auth_service.verify_password",
            return_value=True,
        ),
        patch.object(
            AuthService,
            "get_user_access_level_info",
            new_callable=AsyncMock,
            return_value={
                "access_level": 1,
                "is_super_admin": False,
                "user_type": "user",
            },
        ),
    ):
        result = await AuthService.authenticate_user(cliente_id, "bob", "secret")

    mock_lookup.assert_awaited_once()
    assert result["usuario_id"] == USER_ID
    assert result["target_cliente_id"] == cliente_id
    assert "contrasena" not in result
