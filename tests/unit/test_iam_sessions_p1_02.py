"""IAM-BE-SESSIONS-P1-02: Idle Timeout del dominio Session Management."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.auth.application.session.revoked_reason import RevokedReason

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
TOKEN_ID = uuid4()
NOW = datetime(2026, 6, 18, 12, 0, 0)


def _token_data(*, last_used_at=None, created_at=None):
    return {
        "token_id": TOKEN_ID,
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "client_type": "web",
        "empresa_id": None,
        "created_at": created_at or NOW - timedelta(minutes=30),
        "last_used_at": last_used_at,
    }


@pytest.mark.parametrize(
    "idle_expired_value,expected",
    [
        (0, False),
        (1, True),
    ],
)
@pytest.mark.asyncio
async def test_is_refresh_token_session_idle_expired_core(idle_expired_value, expected):
    from app.infrastructure.database.queries.auth.refresh_token_queries_core import (
        is_refresh_token_session_idle_expired_core,
    )

    mock_query = AsyncMock(return_value=[{"idle_expired": idle_expired_value}])
    with patch(
        "app.infrastructure.database.queries_async.execute_query",
        mock_query,
    ):
        result = await is_refresh_token_session_idle_expired_core(
            TOKEN_ID, CLIENTE_ID, 60
        )

    assert result is expected


@pytest.mark.asyncio
async def test_is_refresh_token_session_idle_expired_core_no_row():
    from app.infrastructure.database.queries.auth.refresh_token_queries_core import (
        is_refresh_token_session_idle_expired_core,
    )

    with patch(
        "app.infrastructure.database.queries_async.execute_query",
        AsyncMock(return_value=[]),
    ):
        result = await is_refresh_token_session_idle_expired_core(
            TOKEN_ID, CLIENTE_ID, 60
        )

    assert result is False


@pytest.mark.asyncio
async def test_is_refresh_token_session_idle_expired_core_disabled_timeout():
    from app.infrastructure.database.queries.auth.refresh_token_queries_core import (
        is_refresh_token_session_idle_expired_core,
    )

    mock_query = AsyncMock()
    result = await is_refresh_token_session_idle_expired_core(
        TOKEN_ID, CLIENTE_ID, 0
    )

    assert result is False
    mock_query.assert_not_called()


@pytest.mark.asyncio
async def test_validate_refresh_token_within_idle_timeout_succeeds():
    token_data = _token_data(last_used_at=NOW - timedelta(minutes=5))
    mock_get = AsyncMock(return_value=token_data)
    mock_idle = AsyncMock(return_value=60)
    mock_idle_core = AsyncMock(return_value=False)
    mock_record = AsyncMock(return_value=True)

    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_core",
        mock_get,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.leer_session_idle_timeout_minutos",
        mock_idle,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.is_refresh_token_session_idle_expired_core",
        mock_idle_core,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.record_refresh_token_activity_core",
        mock_record,
    ), patch.object(
        RefreshTokenService,
        "_call_stack_contains",
        return_value=False,
    ):
        result = await RefreshTokenService.validate_refresh_token(
            "fake-token", cliente_id=CLIENTE_ID
        )

    assert result == token_data
    mock_idle_core.assert_awaited_once_with(TOKEN_ID, CLIENTE_ID, 60)
    mock_record.assert_awaited_once()


@pytest.mark.asyncio
async def test_validate_refresh_token_idle_expired_revokes_and_returns_none():
    token_data = _token_data(last_used_at=NOW - timedelta(minutes=120))
    mock_get = AsyncMock(return_value=token_data)
    mock_idle = AsyncMock(return_value=60)
    mock_idle_core = AsyncMock(return_value=True)
    mock_revoke = AsyncMock(return_value=True)
    mock_record = AsyncMock(return_value=True)

    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_core",
        mock_get,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.leer_session_idle_timeout_minutos",
        mock_idle,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.is_refresh_token_session_idle_expired_core",
        mock_idle_core,
    ), patch.object(
        RefreshTokenService,
        "revoke_token",
        mock_revoke,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.record_refresh_token_activity_core",
        mock_record,
    ), patch.object(
        RefreshTokenService,
        "_call_stack_contains",
        return_value=False,
    ):
        result = await RefreshTokenService.validate_refresh_token(
            "fake-token", cliente_id=CLIENTE_ID
        )

    assert result is None
    mock_revoke.assert_awaited_once_with(
        CLIENTE_ID,
        USUARIO_ID,
        "fake-token",
        revoked_reason=RevokedReason.IDLE_TIMEOUT,
    )
    mock_record.assert_not_awaited()


@pytest.mark.asyncio
async def test_validate_refresh_token_uses_created_at_when_no_last_used_at():
    token_data = _token_data(
        last_used_at=None,
        created_at=NOW - timedelta(minutes=120),
    )
    mock_get = AsyncMock(return_value=token_data)
    mock_idle = AsyncMock(return_value=60)
    mock_idle_core = AsyncMock(return_value=True)
    mock_revoke = AsyncMock(return_value=True)

    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_core",
        mock_get,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.leer_session_idle_timeout_minutos",
        mock_idle,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.is_refresh_token_session_idle_expired_core",
        mock_idle_core,
    ), patch.object(
        RefreshTokenService,
        "revoke_token",
        mock_revoke,
    ), patch.object(
        RefreshTokenService,
        "_call_stack_contains",
        return_value=False,
    ):
        result = await RefreshTokenService.validate_refresh_token(
            "fake-token", cliente_id=CLIENTE_ID
        )

    assert result is None
    mock_idle_core.assert_awaited_once_with(TOKEN_ID, CLIENTE_ID, 60)
    mock_revoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_validate_refresh_token_skips_idle_when_timeout_disabled():
    token_data = _token_data(last_used_at=NOW - timedelta(days=5))
    mock_get = AsyncMock(return_value=token_data)
    mock_idle = AsyncMock(return_value=None)
    mock_idle_core = AsyncMock(return_value=True)
    mock_record = AsyncMock(return_value=True)

    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_core",
        mock_get,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.leer_session_idle_timeout_minutos",
        mock_idle,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.is_refresh_token_session_idle_expired_core",
        mock_idle_core,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.record_refresh_token_activity_core",
        mock_record,
    ), patch.object(
        RefreshTokenService,
        "_call_stack_contains",
        return_value=False,
    ):
        result = await RefreshTokenService.validate_refresh_token(
            "fake-token", cliente_id=CLIENTE_ID
        )

    assert result == token_data
    mock_idle_core.assert_not_awaited()
    mock_record.assert_awaited_once()


@pytest.mark.asyncio
async def test_validate_refresh_token_skips_idle_on_logout_context():
    token_data = _token_data(last_used_at=NOW - timedelta(days=5))
    mock_get = AsyncMock(return_value=token_data)
    mock_idle = AsyncMock(return_value=60)
    mock_idle_core = AsyncMock(return_value=True)
    mock_revoke = AsyncMock(return_value=True)

    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_core",
        mock_get,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.leer_session_idle_timeout_minutos",
        mock_idle,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.is_refresh_token_session_idle_expired_core",
        mock_idle_core,
    ), patch.object(
        RefreshTokenService,
        "revoke_token",
        mock_revoke,
    ), patch.object(
        RefreshTokenService,
        "_call_stack_contains",
        return_value=True,
    ):
        result = await RefreshTokenService.validate_refresh_token(
            "fake-token", cliente_id=CLIENTE_ID
        )

    assert result == token_data
    mock_idle.assert_not_awaited()
    mock_idle_core.assert_not_awaited()
    mock_revoke.assert_not_awaited()


@pytest.mark.asyncio
async def test_leer_session_idle_timeout_minutos_null_and_zero_are_disabled():
    from app.modules.auth.application.services.auth_config_service import (
        leer_session_idle_timeout_minutos,
    )

    mock_query = AsyncMock(side_effect=[[{"session_idle_timeout_minutes": None}], []])

    with patch(
        "app.modules.auth.application.services.auth_config_service.execute_query",
        mock_query,
    ):
        assert await leer_session_idle_timeout_minutos(CLIENTE_ID) is None
        assert await leer_session_idle_timeout_minutos(uuid4()) is None

    mock_query_zero = AsyncMock(return_value=[{"session_idle_timeout_minutes": 0}])
    with patch(
        "app.modules.auth.application.services.auth_config_service.execute_query",
        mock_query_zero,
    ):
        assert await leer_session_idle_timeout_minutos(CLIENTE_ID) is None


@pytest.mark.asyncio
async def test_is_revoked_refresh_reuse_candidate_idle_timeout_is_false():
    row = {
        "is_revoked": True,
        "revoked_reason": RevokedReason.IDLE_TIMEOUT,
    }
    assert RefreshTokenService.is_revoked_refresh_reuse_candidate(row) is False


@pytest.mark.asyncio
async def test_is_revoked_refresh_reuse_candidate_session_rotated_is_true():
    row = {
        "is_revoked": True,
        "revoked_reason": RevokedReason.SESSION_ROTATED,
    }
    assert RefreshTokenService.is_revoked_refresh_reuse_candidate(row) is True


@pytest.mark.asyncio
async def test_leer_session_idle_timeout_minutos_returns_positive_value():
    from app.modules.auth.application.services.auth_config_service import (
        leer_session_idle_timeout_minutos,
    )

    mock_query = AsyncMock(return_value=[{"session_idle_timeout_minutes": 45}])
    with patch(
        "app.modules.auth.application.services.auth_config_service.execute_query",
        mock_query,
    ):
        assert await leer_session_idle_timeout_minutos(CLIENTE_ID) == 45
