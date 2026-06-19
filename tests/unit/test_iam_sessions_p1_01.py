"""IAM-BE-SESSIONS-P1-01: Activity Tracking del dominio Session Management."""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.auth.application.session.revoked_reason import RevokedReason

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
TOKEN_ID = uuid4()


@pytest.mark.asyncio
async def test_validate_refresh_token_records_activity_after_success():
    token_data = {
        "token_id": TOKEN_ID,
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "client_type": "web",
        "empresa_id": None,
    }
    mock_get = AsyncMock(return_value=token_data)
    mock_record = AsyncMock(return_value=True)

    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_core",
        mock_get,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.leer_session_idle_timeout_minutos",
        AsyncMock(return_value=None),
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
    mock_get.assert_awaited_once()
    mock_record.assert_awaited_once_with(TOKEN_ID, CLIENTE_ID)


@pytest.mark.asyncio
async def test_validate_refresh_token_skips_activity_on_logout_context():
    token_data = {
        "token_id": TOKEN_ID,
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "client_type": "web",
        "empresa_id": None,
    }
    mock_get = AsyncMock(return_value=token_data)
    mock_record = AsyncMock(return_value=True)

    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_core",
        mock_get,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.leer_session_idle_timeout_minutos",
        AsyncMock(return_value=None),
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.record_refresh_token_activity_core",
        mock_record,
    ), patch.object(
        RefreshTokenService,
        "_call_stack_contains",
        return_value=True,
    ):
        result = await RefreshTokenService.validate_refresh_token(
            "fake-token", cliente_id=CLIENTE_ID
        )

    assert result == token_data
    mock_record.assert_not_awaited()


@pytest.mark.asyncio
async def test_validate_refresh_token_does_not_record_when_invalid():
    mock_get = AsyncMock(return_value=None)
    mock_record = AsyncMock(return_value=True)

    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_core",
        mock_get,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.leer_session_idle_timeout_minutos",
        AsyncMock(return_value=None),
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.record_refresh_token_activity_core",
        mock_record,
    ):
        result = await RefreshTokenService.validate_refresh_token(
            "invalid", cliente_id=CLIENTE_ID
        )

    assert result is None
    mock_record.assert_not_awaited()


@pytest.mark.asyncio
async def test_record_refresh_token_activity_core_increments_uso_count():
    from app.infrastructure.database.queries.auth.refresh_token_queries_core import (
        record_refresh_token_activity_core,
    )

    mock_update = AsyncMock(return_value={"rows_affected": 1})

    with patch(
        "app.infrastructure.database.queries_async.execute_update",
        mock_update,
    ):
        ok = await record_refresh_token_activity_core(TOKEN_ID, CLIENTE_ID)

    assert ok is True
    mock_update.assert_awaited_once()
    query = mock_update.await_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "last_used_at" in compiled.lower() or "last_used_at" in str(query)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method_name,core_name,reason,extra_kwargs",
    [
        (
            "revoke_token",
            "revoke_refresh_token_core",
            RevokedReason.USER_LOGOUT,
            {"usuario_id": USUARIO_ID, "token": "abc"},
        ),
        (
            "revoke_all_user_tokens",
            "revoke_all_user_tokens_core",
            RevokedReason.LOGOUT_ALL,
            {},
        ),
        (
            "revoke_refresh_token_by_id",
            "revoke_refresh_token_by_id_core",
            RevokedReason.ADMIN_REVOKE,
            {},
        ),
    ],
)
async def test_revoke_methods_pass_revoked_reason_to_core(
    method_name, core_name, reason, extra_kwargs
):
    mock_core = AsyncMock(
        return_value={"token_id": TOKEN_ID, "is_revoked": True}
        if method_name != "revoke_all_user_tokens"
        else 2
    )

    with patch(
        f"app.modules.auth.application.services.refresh_token_service.{core_name}",
        mock_core,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.get_current_client_id",
        return_value=CLIENTE_ID,
    ):
        method = getattr(RefreshTokenService, method_name)
        if method_name == "revoke_refresh_token_by_id":
            await method(TOKEN_ID, revoked_reason=reason)
        elif method_name == "revoke_all_user_tokens":
            await method(CLIENTE_ID, USUARIO_ID, revoked_reason=reason)
        else:
            await method(
                CLIENTE_ID,
                USUARIO_ID,
                extra_kwargs["token"],
                revoked_reason=reason,
            )

    mock_core.assert_awaited_once()
    assert mock_core.await_args.kwargs["revoked_reason"] == str(reason)


@pytest.mark.asyncio
async def test_handle_revoked_refresh_reuse_uses_token_reuse_reason():
    mock_revoke = AsyncMock(return_value=2)
    mock_blacklist = AsyncMock(return_value=1)

    with patch(
        "app.modules.auth.application.services.refresh_token_service.AuditService.registrar_auth_event",
        AsyncMock(),
    ), patch.object(
        RefreshTokenService,
        "revoke_all_user_tokens",
        mock_revoke,
    ), patch.object(
        RefreshTokenService,
        "blacklist_access_for_user_active_sessions",
        mock_blacklist,
    ):
        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError):
            await RefreshTokenService.handle_revoked_refresh_reuse(
                cliente_id=CLIENTE_ID,
                usuario_id=USUARIO_ID,
                username="admin",
            )

    mock_revoke.assert_awaited_once_with(
        CLIENTE_ID, USUARIO_ID, revoked_reason=RevokedReason.TOKEN_REUSE
    )


@pytest.mark.asyncio
async def test_revoked_reason_enum_values_are_stable():
    expected = {
        "USER_LOGOUT",
        "LOGOUT_ALL",
        "ADMIN_REVOKE",
        "PASSWORD_CHANGE",
        "USER_DEACTIVATED",
        "USER_DELETED",
        "TOKEN_REUSE",
        "SESSION_ROTATED",
        "IDLE_TIMEOUT",
        "SESSION_LIMIT",
    }
    assert {r.value for r in RevokedReason} == expected
