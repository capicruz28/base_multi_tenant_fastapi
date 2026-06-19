"""IAM-BE-SESSIONS-P1-02-HOTFIX-02: regresión idle timeout (reloj SQL único)."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.application.services.refresh_token_service import RefreshTokenService
from app.modules.auth.application.session.revoked_reason import RevokedReason

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
TOKEN_ID = uuid4()
LOGIN_AT = datetime(2026, 6, 18, 21, 56, 24)


def _login_token_row(*, minutes_since_login: int):
    return {
        "token_id": TOKEN_ID,
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "client_type": "web",
        "empresa_id": None,
        "created_at": LOGIN_AT,
        "last_used_at": None,
    }


def _refresh_jwt_payload():
    return {
        "sub": "admin",
        "cliente_id": str(CLIENTE_ID),
        "type": "refresh",
        "access_level": 1,
        "user_type": "user",
        "is_super_admin": False,
    }


@pytest.mark.asyncio
async def test_login_plus_five_minutes_refresh_not_idle_timeout_validate_succeeds():
    """
    Login → 5 min → Refresh: SQL idle no expirado → validate OK (camino HTTP 200).
    """
    token_data = _login_token_row(minutes_since_login=5)
    mock_get = AsyncMock(return_value=token_data)
    mock_idle_cfg = AsyncMock(return_value=60)
    mock_idle_sql = AsyncMock(return_value=False)
    mock_record = AsyncMock(return_value=True)

    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_core",
        mock_get,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.leer_session_idle_timeout_minutos",
        mock_idle_cfg,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.is_refresh_token_session_idle_expired_core",
        mock_idle_sql,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.record_refresh_token_activity_core",
        mock_record,
    ), patch.object(
        RefreshTokenService,
        "_call_stack_contains",
        return_value=False,
    ):
        result = await RefreshTokenService.validate_refresh_token(
            "refresh-jwt-after-login", cliente_id=CLIENTE_ID
        )

    assert result == token_data
    mock_idle_sql.assert_awaited_once_with(TOKEN_ID, CLIENTE_ID, 60)


@pytest.mark.asyncio
async def test_login_plus_five_minutes_refresh_http_200_path_via_depends():
    """
    Login → 5 min → Refresh: Depends no lanza 401 (camino HTTP 200 del endpoint).
    """
    request = MagicMock()
    request.headers.get.return_value = "web"
    request.client.host = "127.0.0.1"

    token_data = _login_token_row(minutes_since_login=5)
    user_row = {
        "usuario_id": USUARIO_ID,
        "nombre_usuario": "admin",
        "es_activo": True,
        "cliente_id": CLIENTE_ID,
    }

    with patch(
        "app.modules.auth.application.services.auth_service.decode_refresh_token",
        return_value=_refresh_jwt_payload(),
    ), patch.object(
        RefreshTokenService,
        "validate_refresh_token",
        AsyncMock(return_value=token_data),
    ), patch.object(
        AuthService,
        "_fetch_user_row_for_refresh",
        AsyncMock(return_value=user_row),
    ):
        result = await AuthService.get_current_user_from_refresh(
            request,
            refresh_token_cookie="refresh-jwt-after-login",
            refresh_token_body=None,
        )

    assert result["nombre_usuario"] == "admin"


@pytest.mark.asyncio
async def test_login_plus_sixty_one_minutes_refresh_idle_timeout_validate_none():
    """
    Login → 61 min → Refresh: SQL idle expirado → revoke IDLE_TIMEOUT → validate None.
    """
    token_data = _login_token_row(minutes_since_login=61)
    mock_get = AsyncMock(return_value=token_data)
    mock_idle_cfg = AsyncMock(return_value=60)
    mock_idle_sql = AsyncMock(return_value=True)
    mock_revoke = AsyncMock(return_value=True)

    with patch(
        "app.modules.auth.application.services.refresh_token_service.get_refresh_token_by_hash_core",
        mock_get,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.leer_session_idle_timeout_minutos",
        mock_idle_cfg,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.is_refresh_token_session_idle_expired_core",
        mock_idle_sql,
    ), patch.object(
        RefreshTokenService,
        "revoke_token",
        mock_revoke,
    ), patch(
        "app.modules.auth.application.services.refresh_token_service.record_refresh_token_activity_core",
        AsyncMock(),
    ), patch.object(
        RefreshTokenService,
        "_call_stack_contains",
        return_value=False,
    ):
        result = await RefreshTokenService.validate_refresh_token(
            "refresh-jwt-after-login", cliente_id=CLIENTE_ID
        )

    assert result is None
    mock_revoke.assert_awaited_once_with(
        CLIENTE_ID,
        USUARIO_ID,
        "refresh-jwt-after-login",
        revoked_reason=RevokedReason.IDLE_TIMEOUT,
    )


@pytest.mark.asyncio
async def test_login_plus_sixty_one_minutes_refresh_http_401_via_depends():
    """
    Login → 61 min → Refresh: validate None por idle → HTTP 401 en Depends.
    """
    request = MagicMock()
    request.headers.get.return_value = "web"
    request.client.host = "127.0.0.1"

    with patch(
        "app.modules.auth.application.services.auth_service.decode_refresh_token",
        return_value=_refresh_jwt_payload(),
    ), patch.object(
        RefreshTokenService,
        "validate_refresh_token",
        AsyncMock(return_value=None),
    ), patch(
        "app.modules.auth.application.services.auth_service.get_refresh_token_by_hash_any_state_core",
        AsyncMock(
            return_value={
                "is_revoked": True,
                "revoked_reason": RevokedReason.IDLE_TIMEOUT,
                "usuario_id": USUARIO_ID,
            }
        ),
    ), patch(
        "app.modules.auth.application.services.auth_service.AuditService.registrar_auth_event",
        AsyncMock(),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.get_current_user_from_refresh(
                request,
                refresh_token_cookie="refresh-jwt-after-login",
                refresh_token_body=None,
            )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_idle_sql_query_uses_getdate_and_datediff():
    """La evaluación idle delegada a SQL usa GETDATE() y DATEDIFF sobre la fila."""
    from app.infrastructure.database.queries.auth.refresh_token_queries_core import (
        is_refresh_token_session_idle_expired_core,
    )

    mock_query = AsyncMock(return_value=[{"idle_expired": 0}])
    with patch(
        "app.infrastructure.database.queries_async.execute_query",
        mock_query,
    ):
        await is_refresh_token_session_idle_expired_core(TOKEN_ID, CLIENTE_ID, 60)

    compiled = str(mock_query.await_args.args[0]).upper()
    assert "GETDATE()" in compiled
    assert "DATEDIFF" in compiled
    assert "COALESCE" in compiled
