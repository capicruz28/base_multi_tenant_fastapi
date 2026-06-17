"""Unit tests — platform identity bootstrap (sin BD)."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.core.exceptions import DatabaseError
from app.modules.tenant.application.services.platform_identity_bootstrap_service import (
    PlatformIdentityBootstrapService,
)


def _mock_result(first=None, scalar=None):
    result = MagicMock()
    result.first.return_value = first
    result.scalar.return_value = scalar
    return result


@pytest.mark.asyncio
async def test_dry_run_reports_would_create_when_missing():
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            _mock_result(None),  # conflict
            _mock_result(None),  # cliente
            _mock_result(None),  # rol
            _mock_result(None),  # usuario
            _mock_result(None),  # auth_config dry-run
        ]
    )
    with patch(
        "app.modules.tenant.application.services.platform_identity_bootstrap_service.settings"
    ) as mock_settings:
        mock_settings.PLATFORM_BOOTSTRAP_INITIAL_PASSWORD = "admin123"
        mock_settings.ENVIRONMENT = "development"
        mock_settings.SUPERADMIN_USERNAME = "superadmin"
        result = await PlatformIdentityBootstrapService.bootstrap_platform_identity(
            session, dry_run=True
        )
    assert "would_create_cliente" in result.actions
    assert "would_create_rol" in result.actions
    assert "would_create_usuario" in result.actions


@pytest.mark.asyncio
async def test_reuse_existing_usuario_does_not_set_password():
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            _mock_result((1,)),  # pre-check cliente_exists
            _mock_result((1,)),  # pre-check rol_exists
            _mock_result((1,)),  # pre-check usuario_exists
            _mock_result(None),  # conflict
            _mock_result((UUID(int=1), True)),  # cliente row
            _mock_result((UUID(int=2),)),  # rol row
            _mock_result((UUID(int=3), True)),  # usuario row
            _mock_result((1,)),  # usuario_rol
            _mock_result((1,)),  # auth_config
        ]
    )
    with (
        patch(
            "app.modules.tenant.application.services.platform_identity_bootstrap_service.settings"
        ) as mock_settings,
        patch(
            "app.modules.tenant.application.services.platform_identity_bootstrap_service.PlatformRbacBootstrapService.resolve_platform_cliente_id",
            return_value=UUID("00000000-0000-0000-0000-000000000001"),
        ),
    ):
        mock_settings.SUPERADMIN_USERNAME = "superadmin"
        mock_settings.SUPERADMIN_CLIENTE_CODIGO = "SUPERADMIN"
        mock_settings.SUPERADMIN_SUBDOMINIO = "platform"
        mock_settings.PLATFORM_BOOTSTRAP_INITIAL_PASSWORD = ""
        mock_settings.PLATFORM_BOOTSTRAP_CONTACT_EMAIL = ""
        mock_settings.PLATFORM_BOOTSTRAP_RAZON_SOCIAL = ""
        mock_settings.SUPERADMIN_CLIENTE_ID = "00000000-0000-0000-0000-000000000001"
        result = await PlatformIdentityBootstrapService.bootstrap_platform_identity(
            session, dry_run=False
        )
    assert result.usuario_created is False
    assert result.password_set is False
    assert "usuario_reused" in result.actions


@pytest.mark.asyncio
async def test_cliente_conflict_raises_database_error():
    session = AsyncMock()
    other_id = UUID(int=99)
    session.execute = AsyncMock(return_value=_mock_result((other_id,)))
    with patch(
        "app.modules.tenant.application.services.platform_identity_bootstrap_service.settings"
    ) as mock_settings:
        mock_settings.SUPERADMIN_SUBDOMINIO = "platform"
        mock_settings.SUPERADMIN_CLIENTE_CODIGO = "SUPERADMIN"
        mock_settings.SUPERADMIN_CLIENTE_ID = "00000000-0000-0000-0000-000000000001"
        with pytest.raises(DatabaseError) as exc:
            await PlatformIdentityBootstrapService.bootstrap_platform_identity(
                session, dry_run=False
            )
    assert exc.value.internal_code == "PLATFORM_CLIENTE_CONFLICT"


def test_prod_requires_password_when_creating_user():
    with patch(
        "app.modules.tenant.application.services.platform_identity_bootstrap_service.settings"
    ) as mock_settings:
        mock_settings.PLATFORM_BOOTSTRAP_INITIAL_PASSWORD = ""
        mock_settings.ENVIRONMENT = "production"
        with pytest.raises(ValueError, match="PLATFORM_BOOTSTRAP_INITIAL_PASSWORD"):
            PlatformIdentityBootstrapService._resolve_initial_password(
                usuario_will_be_created=True
            )
