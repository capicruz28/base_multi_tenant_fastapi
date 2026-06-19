"""IAM-BE-SESSIONS-P1-03: Max Active Sessions enforcement."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.auth.application.session.revoked_reason import RevokedReason

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()


def _session(token_id, *, minutes_ago: int, device: str = "web"):
    return {
        "token_id": token_id,
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "created_at": datetime.utcnow() - timedelta(minutes=minutes_ago),
        "device_name": device,
        "client_type": "web",
    }


@pytest.mark.parametrize(
    "active_count,max_active,expected",
    [
        (0, 3, 0),
        (2, 3, 0),
        (3, 3, 1),
        (4, 3, 2),
        (5, 0, 0),
        (5, -1, 0),
    ],
)
def test_sessions_to_revoke_for_limit(active_count, max_active, expected):
    assert (
        RefreshTokenService._sessions_to_revoke_for_limit(active_count, max_active)
        == expected
    )


@pytest.mark.asyncio
async def test_enforce_max_active_sessions_disabled():
    with patch(
        "app.modules.auth.application.services.refresh_token_service.leer_max_active_sessions",
        AsyncMock(return_value=None),
    ):
        revoked = await RefreshTokenService.enforce_max_active_sessions(
            CLIENTE_ID, USUARIO_ID
        )
    assert revoked == 0


@pytest.mark.asyncio
async def test_enforce_max_active_sessions_under_limit():
    t1 = uuid4()
    sessions = [_session(t1, minutes_ago=60)]
    mock_revoke = AsyncMock(return_value={"token_id": t1})

    with patch(
        "app.modules.auth.application.services.refresh_token_service.leer_max_active_sessions",
        AsyncMock(return_value=3),
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.get_active_sessions_by_user_oldest_first_core",
        AsyncMock(return_value=sessions),
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.revoke_refresh_token_by_id_core",
        mock_revoke,
    ):
        revoked = await RefreshTokenService.enforce_max_active_sessions(
            CLIENTE_ID, USUARIO_ID
        )

    assert revoked == 0
    mock_revoke.assert_not_awaited()


@pytest.mark.asyncio
async def test_enforce_max_active_sessions_at_limit_revokes_oldest():
    oldest = uuid4()
    middle = uuid4()
    newest = uuid4()
    sessions = [
        _session(oldest, minutes_ago=120, device="mobile-a"),
        _session(middle, minutes_ago=60, device="mobile-b"),
        _session(newest, minutes_ago=10, device="web"),
    ]
    mock_revoke = AsyncMock(return_value={"token_id": oldest})

    with patch(
        "app.modules.auth.application.services.refresh_token_service.leer_max_active_sessions",
        AsyncMock(return_value=3),
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.get_active_sessions_by_user_oldest_first_core",
        AsyncMock(return_value=sessions),
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.revoke_refresh_token_by_id_core",
        mock_revoke,
    ):
        revoked = await RefreshTokenService.enforce_max_active_sessions(
            CLIENTE_ID, USUARIO_ID
        )

    assert revoked == 1
    mock_revoke.assert_awaited_once_with(
        oldest,
        CLIENTE_ID,
        revoked_reason=str(RevokedReason.SESSION_LIMIT),
    )


@pytest.mark.asyncio
async def test_enforce_max_active_sessions_over_limit_revokes_multiple_oldest():
    ids = [uuid4() for _ in range(4)]
    sessions = [_session(tid, minutes_ago=i * 10) for i, tid in enumerate(ids)]
    mock_revoke = AsyncMock(return_value={"token_id": ids[0]})

    with patch(
        "app.modules.auth.application.services.refresh_token_service.leer_max_active_sessions",
        AsyncMock(return_value=3),
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.get_active_sessions_by_user_oldest_first_core",
        AsyncMock(return_value=sessions),
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.revoke_refresh_token_by_id_core",
        mock_revoke,
    ):
        revoked = await RefreshTokenService.enforce_max_active_sessions(
            CLIENTE_ID, USUARIO_ID
        )

    assert revoked == 2
    assert mock_revoke.await_count == 2
    mock_revoke.assert_any_await(
        ids[0], CLIENTE_ID, revoked_reason=str(RevokedReason.SESSION_LIMIT)
    )
    mock_revoke.assert_any_await(
        ids[1], CLIENTE_ID, revoked_reason=str(RevokedReason.SESSION_LIMIT)
    )


@pytest.mark.asyncio
async def test_store_refresh_token_enforces_limit_before_insert():
    mock_enforce = AsyncMock(return_value=1)
    mock_insert = AsyncMock(return_value={"token_id": uuid4()})

    with patch.object(
        RefreshTokenService,
        "enforce_max_active_sessions",
        mock_enforce,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.insert_refresh_token_core",
        mock_insert,
    ):
        result = await RefreshTokenService.store_refresh_token(
            CLIENTE_ID,
            USUARIO_ID,
            "new-refresh-token",
            is_rotation=False,
        )

    assert result["token_id"] is not None
    mock_enforce.assert_awaited_once_with(CLIENTE_ID, USUARIO_ID)
    mock_insert.assert_awaited_once()


@pytest.mark.asyncio
async def test_store_refresh_token_skips_limit_on_rotation():
    mock_enforce = AsyncMock(return_value=0)
    mock_insert = AsyncMock(return_value={"token_id": uuid4()})

    with patch.object(
        RefreshTokenService,
        "enforce_max_active_sessions",
        mock_enforce,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_core",
        AsyncMock(return_value=None),
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.insert_refresh_token_core",
        mock_insert,
    ):
        await RefreshTokenService.store_refresh_token(
            CLIENTE_ID,
            USUARIO_ID,
            "rotated-token",
            is_rotation=True,
        )

    mock_enforce.assert_not_awaited()
    mock_insert.assert_awaited_once()


@pytest.mark.asyncio
async def test_store_refresh_token_rotation_duplicate_skips_enforce_and_insert():
    existing_id = uuid4()
    mock_enforce = AsyncMock()
    mock_insert = AsyncMock()

    with patch.object(
        RefreshTokenService,
        "enforce_max_active_sessions",
        mock_enforce,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_core",
        AsyncMock(return_value={"token_id": existing_id}),
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.insert_refresh_token_core",
        mock_insert,
    ):
        result = await RefreshTokenService.store_refresh_token(
            CLIENTE_ID,
            USUARIO_ID,
            "dup-token",
            is_rotation=True,
        )

    assert result["token_id"] == existing_id
    mock_enforce.assert_not_awaited()
    mock_insert.assert_not_awaited()


@pytest.mark.asyncio
async def test_leer_max_active_sessions_null_and_zero_disabled():
    from app.modules.auth.application.services.auth_config_service import (
        leer_max_active_sessions,
    )

    with patch(
        "app.modules.auth.application.services.auth_config_service.execute_query",
        AsyncMock(side_effect=[[{"max_active_sessions": None}], []]),
    ):
        assert await leer_max_active_sessions(CLIENTE_ID) is None
        assert await leer_max_active_sessions(uuid4()) is None

    with patch(
        "app.modules.auth.application.services.auth_config_service.execute_query",
        AsyncMock(return_value=[{"max_active_sessions": 0}]),
    ):
        assert await leer_max_active_sessions(CLIENTE_ID) is None


@pytest.mark.asyncio
async def test_leer_max_active_sessions_returns_positive():
    from app.modules.auth.application.services.auth_config_service import (
        leer_max_active_sessions,
    )

    with patch(
        "app.modules.auth.application.services.auth_config_service.execute_query",
        AsyncMock(return_value=[{"max_active_sessions": 3}]),
    ):
        assert await leer_max_active_sessions(CLIENTE_ID) == 3


@pytest.mark.asyncio
async def test_revoked_reason_includes_session_limit():
    assert RevokedReason.SESSION_LIMIT == "SESSION_LIMIT"
