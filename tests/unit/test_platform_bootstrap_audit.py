"""Unit tests — platform bootstrap audit flags."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.modules.tenant.application.services.platform_bootstrap_audit import audit_platform_ready

PLATFORM_CID = UUID("00000000-0000-0000-0000-000000000001")


def _mock_result(first=None, scalar=None):
    result = MagicMock()
    result.first.return_value = first
    result.scalar.return_value = scalar
    return result


@pytest.mark.asyncio
async def test_needs_bootstrap_when_identity_missing():
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            _mock_result(None),  # cliente
            _mock_result(None),  # rol
            _mock_result(None),  # usuario
            _mock_result(None),  # auth_config
            _mock_result(scalar=0),  # cm_sysadmin
            _mock_result((1,)),  # perm_platform active
        ]
    )
    with (
        patch(
            "app.modules.tenant.application.services.platform_bootstrap_audit.settings.SUPERADMIN_USERNAME",
            "superadmin",
        ),
        patch(
            "app.modules.tenant.application.services.platform_bootstrap_audit.PlatformRbacBootstrapService.resolve_platform_cliente_id",
            return_value=PLATFORM_CID,
        ),
    ):
        snap = await audit_platform_ready(session)
    assert snap["needs_identity"] is True
    assert snap["needs_bootstrap"] is True


@pytest.mark.asyncio
async def test_ready_when_identity_and_rbac_ok():
    rol_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            _mock_result((str(PLATFORM_CID), "SUPERADMIN", "platform", True)),
            _mock_result((rol_id,)),
            _mock_result(("user-id", "superadmin", True)),
            _mock_result((1,)),  # usuario_rol
            _mock_result((1,)),  # auth_config
            _mock_result(scalar=10),  # rp_count
            _mock_result((1,)),  # has_core_rp
            _mock_result((1,)),  # has_tenant_cliente_crear
            _mock_result(scalar=1),  # cm_sysadmin
            _mock_result((1,)),  # perm_platform
        ]
    )
    with (
        patch(
            "app.modules.tenant.application.services.platform_bootstrap_audit.settings.SUPERADMIN_USERNAME",
            "superadmin",
        ),
        patch(
            "app.modules.tenant.application.services.platform_bootstrap_audit.PlatformRbacBootstrapService.resolve_platform_cliente_id",
            return_value=PLATFORM_CID,
        ),
    ):
        snap = await audit_platform_ready(session)
    assert snap["needs_identity"] is False
    assert snap["needs_rbac"] is False
    assert snap["needs_bootstrap"] is False
