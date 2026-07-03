"""F6-P2a — Identity Gateway access level migration."""
from __future__ import annotations

from typing import Set
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.core.identity.identity_context import IdentityContext
from app.core.identity.identity_gateway import IdentityGateway
from app.core.identity.identity_scope import IdentityScope
from app.core.tenant.context import reset_tenant_context, set_tenant_context
from tests.integration.helpers.hybrid_mock_metadata import (
    build_dedicated_metadata,
    build_shared_metadata,
    build_tenant_context,
)

SHARED_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
DEDICATED_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
USER_ID = UUID("11111111-1111-4111-8111-111111111111")


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
def test_map_access_level_row_tenant_admin():
    info = IdentityGateway._map_access_level_row(
        {"max_level": 4, "super_admin_count": 0, "total_roles": 1}
    )
    assert info["access_level"] == 4
    assert info["user_type"] == "tenant_admin"
    assert info["is_super_admin"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_access_level_info_row_scoped_executor(shared_tenant_context):
    ctx = IdentityContext(cliente_id=SHARED_ID)
    mock_row = {"max_level": 5, "super_admin_count": 0, "total_roles": 2}

    with patch(
        "app.core.identity.identity_gateway.execute_identity_query",
        new_callable=AsyncMock,
    ) as mock_exec:
        mock_exec.return_value = [mock_row]
        info = await IdentityGateway.get_user_access_level_info(ctx, USER_ID)

    assert info["access_level"] == 5
    mock_exec.assert_awaited_once()
    assert mock_exec.call_args.kwargs["identity_scope"] == IdentityScope.ROW_SCOPED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_access_level_info_engine_scoped_executor(dedicated_tenant_context):
    ctx = IdentityContext(cliente_id=DEDICATED_ID)
    mock_row = {"max_level": 5, "super_admin_count": 0, "total_roles": 1}

    with patch(
        "app.core.identity.identity_gateway.execute_identity_query",
        new_callable=AsyncMock,
    ) as mock_exec:
        mock_exec.return_value = [mock_row]
        info = await IdentityGateway.get_user_access_level_info(ctx, USER_ID)

    assert info["user_type"] == "tenant_admin"
    mock_exec.assert_awaited_once()
    assert mock_exec.call_args.kwargs["identity_scope"] == IdentityScope.ENGINE_SCOPED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_auth_service_delegates_access_level_to_identity_gateway():
    from app.modules.auth.application.services.auth_service import AuthService

    with (
        patch.object(
            AuthService,
            "_detect_platform_superadmin",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "app.core.identity.identity_gateway.IdentityGateway.get_user_access_level_info",
            new_callable=AsyncMock,
            return_value={
                "access_level": 4,
                "is_super_admin": False,
                "user_type": "tenant_admin",
            },
        ) as mock_ig,
    ):
        info = await AuthService.get_user_access_level_info(USER_ID, SHARED_ID)

    mock_ig.assert_awaited_once()
    assert info["user_type"] == "tenant_admin"


@pytest.mark.unit
def test_row_scoped_query_has_cliente_and_rol_filters():
    from app.infrastructure.identity.queries.user_identity_queries import (
        select_user_access_level_row_scoped,
    )

    query = select_user_access_level_row_scoped(
        usuario_id=USER_ID,
        cliente_id=SHARED_ID,
    )
    compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "usuario_rol" in compiled.lower()
    assert "rol" in compiled.lower()


@pytest.mark.unit
def test_engine_scoped_query_has_no_cliente_id_on_rol():
    from app.infrastructure.identity.queries.user_identity_queries import (
        select_user_access_level_engine_scoped,
        select_user_access_level_row_scoped,
    )

    row = select_user_access_level_row_scoped(
        usuario_id=USER_ID,
        cliente_id=SHARED_ID,
    )
    eng = select_user_access_level_engine_scoped(usuario_id=USER_ID)
    row_sql = str(row.compile(compile_kwargs={"literal_binds": True})).lower()
    eng_sql = str(eng.compile(compile_kwargs={"literal_binds": True})).lower()
    assert "cliente_id" in row_sql
    assert "cliente_id" not in eng_sql
