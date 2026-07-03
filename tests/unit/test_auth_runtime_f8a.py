"""F8-A — Auth Runtime: IdentityGateway + OrgReadGateway extensions."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.core.auth.auth_runtime_scope import resolve_rbac_database_type
from app.core.identity.identity_context import IdentityContext
from app.core.identity.identity_gateway import IdentityGateway
from app.core.identity.identity_scope import IdentityScope
from app.core.organization.org_read_gateway import OrgReadGateway
from app.core.tenant.context import reset_tenant_context, set_tenant_context
from tests.integration.helpers.hybrid_mock_metadata import (
    build_dedicated_metadata,
    build_shared_metadata,
    build_tenant_context,
)

SHARED_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
DEDICATED_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPRESA_ID = UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")


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


def test_resolve_rbac_database_type_shared(shared_tenant_context):
    assert resolve_rbac_database_type() == "single"
    assert IdentityGateway.resolve_identity_scope() == IdentityScope.ROW_SCOPED


def test_resolve_rbac_database_type_dedicated(dedicated_tenant_context):
    assert resolve_rbac_database_type() == "multi"
    assert IdentityGateway.resolve_identity_scope() == IdentityScope.ENGINE_SCOPED


@pytest.mark.asyncio
async def test_get_user_role_names_delegates_to_identity_query(shared_tenant_context):
    ctx = IdentityContext(cliente_id=SHARED_ID)
    with patch(
        "app.core.identity.identity_gateway.execute_identity_query",
        new_callable=AsyncMock,
    ) as mock_exec:
        mock_exec.return_value = [{"nombre": "Admin"}, {"nombre": "User"}]
        names = await IdentityGateway.get_user_role_names(ctx, USER_ID)
        assert names == ["Admin", "User"]
        mock_exec.assert_awaited_once()


@pytest.mark.asyncio
async def test_org_read_gateway_filters_inactive_empresas():
    active_id = EMPRESA_ID
    inactive_id = UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")
    with patch(
        "app.core.organization.org_read_gateway.get_empresas_by_ids",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = [
            {
                "empresa_id": active_id,
                "razon_social": "Activa SA",
                "nombre_comercial": "Activa",
                "es_activo": True,
            },
            {
                "empresa_id": inactive_id,
                "razon_social": "Inactiva SA",
                "nombre_comercial": "Inactiva",
                "es_activo": False,
            },
        ]
        rows = await OrgReadGateway.get_active_empresas_by_ids(
            SHARED_ID,
            [active_id, inactive_id],
        )
        assert len(rows) == 1
        assert rows[0]["empresa_id"] == active_id


@pytest.mark.asyncio
async def test_is_empresa_active():
    with patch(
        "app.core.organization.org_read_gateway.get_empresa_by_id",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = {"empresa_id": EMPRESA_ID, "es_activo": True}
        assert await OrgReadGateway.is_empresa_active(SHARED_ID, EMPRESA_ID) is True
        mock_get.return_value = None
        assert await OrgReadGateway.is_empresa_active(SHARED_ID, EMPRESA_ID) is False
