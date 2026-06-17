"""Unit tests — platform bootstrap orchestrator."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.tenant.application.services.platform_bootstrap_service import (
    PlatformBootstrapService,
)


@pytest.mark.asyncio
async def test_audit_only_returns_snapshot():
    audit = {"needs_bootstrap": True, "needs_identity": True}
    with patch(
        "app.modules.tenant.application.services.platform_bootstrap_service.get_db_connection"
    ) as mock_conn:
        session = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = session
        with patch(
            "app.modules.tenant.application.services.platform_bootstrap_service.audit_platform_ready",
            new_callable=AsyncMock,
            return_value=audit,
        ):
            result = await PlatformBootstrapService.audit_only()
    assert result == audit


@pytest.mark.asyncio
async def test_apply_runs_identity_then_rbac_in_transaction():
    audit_before = {"needs_bootstrap": True}
    audit_after = {"needs_bootstrap": False}
    identity_dict = {
        "cliente_created": True,
        "usuario_id": "11111111-1111-1111-1111-111111111111",
    }
    rbac_dict = {"grants": {"inserted": 5}}

    session = AsyncMock()
    begin_cm = MagicMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)

    with patch(
        "app.modules.tenant.application.services.platform_bootstrap_service.get_db_connection"
    ) as mock_conn:
        mock_conn.return_value.__aenter__.return_value = session
        with patch(
            "app.modules.tenant.application.services.platform_bootstrap_service.audit_platform_ready",
            new_callable=AsyncMock,
            side_effect=[audit_before, audit_after],
        ):
            with patch(
                "app.modules.tenant.application.services.platform_bootstrap_service.PlatformIdentityBootstrapService.bootstrap_platform_identity",
                new_callable=AsyncMock,
            ) as mock_identity:
                identity_result = MagicMock()
                identity_result.to_dict.return_value = identity_dict
                mock_identity.return_value = identity_result
                with patch(
                    "app.modules.tenant.application.services.platform_bootstrap_service.PlatformRbacBootstrapService.bootstrap_platform_rbac",
                    new_callable=AsyncMock,
                    return_value=rbac_dict,
                ) as mock_rbac:
                    report = await PlatformBootstrapService.bootstrap(mode="apply")

    mock_identity.assert_awaited_once()
    mock_rbac.assert_awaited_once()
    session.begin.assert_called_once()
    assert report.success is True
    assert report.identity == identity_dict
    assert report.rbac == rbac_dict


@pytest.mark.asyncio
async def test_rbac_only_skips_identity():
    audit_before = {"needs_bootstrap": True, "needs_rbac": True}
    audit_after = {"needs_bootstrap": False}
    session = AsyncMock()
    begin_cm = MagicMock()
    begin_cm.__aenter__ = AsyncMock(return_value=None)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)

    with patch(
        "app.modules.tenant.application.services.platform_bootstrap_service.get_db_connection"
    ) as mock_conn:
        mock_conn.return_value.__aenter__.return_value = session
        with patch(
            "app.modules.tenant.application.services.platform_bootstrap_service.audit_platform_ready",
            new_callable=AsyncMock,
            side_effect=[audit_before, audit_after],
        ):
            with patch(
                "app.modules.tenant.application.services.platform_bootstrap_service.PlatformIdentityBootstrapService.bootstrap_platform_identity",
                new_callable=AsyncMock,
            ) as mock_identity:
                with patch(
                    "app.modules.tenant.application.services.platform_bootstrap_service.PlatformRbacBootstrapService.bootstrap_platform_rbac",
                    new_callable=AsyncMock,
                    return_value={"ok": True},
                ):
                    report = await PlatformBootstrapService.bootstrap(
                        mode="apply", rbac_only=True
                    )
    mock_identity.assert_not_awaited()
    assert report.identity.get("skipped") is True
