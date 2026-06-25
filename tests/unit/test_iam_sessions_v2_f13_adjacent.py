"""F13 — ecosistema adyacente: C05, C14, UserService, SuperAdmin, JWT sid, deps."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security.jwt import create_access_token
from app.modules.auth.application.services.business_activity_service import (
    BUSINESS_ACTIVITY_THROTTLE_MINUTES,
    BusinessActivityService,
)
from app.modules.auth.application.services.refresh_token_cleanup_job import (
    RefreshTokenCleanupJob,
)
from app.modules.auth.application.session.revoked_reason import RevokedReason
from app.modules.auth.presentation.schemas_sessions import (
    SessionDeviceRead,
    UserSessionRead,
)
from app.modules.superadmin.application.services.superadmin_usuario_service import (
    SuperadminUsuarioService,
)
from app.modules.users.application.services.user_service import UsuarioService

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
SESSION_ID = uuid4()
TOKEN_ID = uuid4()
NOW = datetime(2026, 6, 22, 12, 0, 0)

_BAS = "app.modules.auth.application.services.business_activity_service"
_FEATURE = f"{_BAS}.is_session_v2_enabled"
_TOUCH_CORE = f"{_BAS}.touch_business_activity_core"
_GET_ACTIVE = f"{_BAS}.get_active_session_by_id_core"
_FEATURE_FLAG = "app.modules.auth.application.session.session_v2_feature.is_session_v2_enabled"
_PURGE_CORE = "app.infrastructure.database.queries.auth.session.purge_expired_tokens_core"
_PURGE_SESSIONS = "app.infrastructure.database.queries.auth.session.purge_closed_sessions_core"
_V1_CLEANUP = (
    "app.modules.auth.application.services.refresh_token_service."
    "RefreshTokenService.cleanup_expired_tokens"
)
_REVOKE_ALL_SESSIONS = (
    "app.modules.auth.application.services.session_revocation_service."
    "SessionRevocationService.revoke_all_sessions"
)
_V1_BLACKLIST = (
    "app.modules.auth.application.services.refresh_token_service."
    "RefreshTokenService.blacklist_access_for_user_active_sessions"
)
_V1_REVOKE_ALL = (
    "app.modules.auth.application.services.refresh_token_service."
    "RefreshTokenService.revoke_all_user_tokens"
)
_C09_LIST = (
    "app.modules.auth.application.services.active_sessions_read_service."
    "ActiveSessionsReadService.list_user_sessions"
)


def _user_session_dto(**overrides) -> UserSessionRead:
    device = SessionDeviceRead(
        client_type="web",
        browser="Chrome",
        browser_version="120",
        os="Windows",
        platform="desktop",
        device_label="Chrome on Windows",
        ip_address="10.0.0.1",
        device_id="dev-1",
    )
    base = dict(
        token_id=TOKEN_ID,
        usuario_id=USUARIO_ID,
        cliente_id=CLIENTE_ID,
        empresa_id=uuid4(),
        issued_at=NOW,
        created_at=NOW,
        last_refresh_at=NOW,
        last_used_at=NOW,
        expires_at=NOW + timedelta(days=7),
        is_current=False,
        status="active",
        duration_seconds=3600,
        device=device,
        client_type="web",
        session_id=SESSION_ID,
        platform="web",
        login_ip="10.0.0.1",
        ip_address="10.0.0.2",
    )
    base.update(overrides)
    return UserSessionRead(**base)


@pytest.mark.unit
def test_f13_business_activity_throttle_skips_touch():
    recent = NOW - timedelta(minutes=BUSINESS_ACTIVITY_THROTTLE_MINUTES - 1)
    assert BusinessActivityService._is_throttled(recent, now=NOW) is True


@pytest.mark.unit
def test_f13_business_activity_throttle_allows_touch_after_window():
    old = NOW - timedelta(minutes=BUSINESS_ACTIVITY_THROTTLE_MINUTES)
    assert BusinessActivityService._is_throttled(old, now=NOW) is False
    assert BusinessActivityService._is_throttled(None, now=NOW) is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f13_business_activity_touch_updates_when_not_throttled():
    with (
        patch(_FEATURE, return_value=True),
        patch(_GET_ACTIVE, new_callable=AsyncMock) as mock_get,
        patch(_TOUCH_CORE, new_callable=AsyncMock) as mock_touch,
    ):
        mock_get.return_value = {
            "session_id": SESSION_ID,
            "last_business_activity_at": NOW - timedelta(minutes=10),
        }
        await BusinessActivityService.touch(SESSION_ID, CLIENTE_ID)

    mock_touch.assert_awaited_once_with(SESSION_ID, CLIENTE_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f13_business_activity_touch_throttled_skips_core():
    recent = datetime.utcnow() - timedelta(minutes=1)
    with (
        patch(_FEATURE, return_value=True),
        patch(_GET_ACTIVE, new_callable=AsyncMock) as mock_get,
        patch(_TOUCH_CORE, new_callable=AsyncMock) as mock_touch,
    ):
        await BusinessActivityService.touch(
            SESSION_ID,
            CLIENTE_ID,
            last_business_activity_at=recent,
        )

    mock_get.assert_not_awaited()
    mock_touch.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f13_business_activity_noop_when_v2_disabled():
    with patch(_FEATURE, return_value=False), patch(
        _TOUCH_CORE, new_callable=AsyncMock
    ) as mock_touch:
        await BusinessActivityService.touch(SESSION_ID, CLIENTE_ID)
    mock_touch.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f13_cleanup_v3_uses_purge_core():
    with (
        patch(_FEATURE_FLAG, return_value=True),
        patch(_PURGE_CORE, new_callable=AsyncMock, return_value=5) as mock_purge,
        patch(_PURGE_SESSIONS, new_callable=AsyncMock, return_value=2) as mock_purge_sessions,
        patch(_V1_CLEANUP, new_callable=AsyncMock) as mock_v1,
    ):
        deleted = await RefreshTokenCleanupJob._purge_tenant_tokens(CLIENTE_ID)

    assert deleted == 7
    mock_purge.assert_awaited_once_with(CLIENTE_ID)
    mock_purge_sessions.assert_awaited_once_with(CLIENTE_ID)
    mock_v1.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f13_cleanup_v1_uses_legacy_service():
    with (
        patch(_FEATURE_FLAG, return_value=False),
        patch(_PURGE_CORE, new_callable=AsyncMock) as mock_purge,
        patch(_PURGE_SESSIONS, new_callable=AsyncMock) as mock_purge_sessions,
        patch(_V1_CLEANUP, new_callable=AsyncMock, return_value=3) as mock_v1,
    ):
        deleted = await RefreshTokenCleanupJob._purge_tenant_tokens(CLIENTE_ID)

    assert deleted == 3
    mock_v1.assert_awaited_once()
    mock_purge.assert_not_awaited()
    mock_purge_sessions.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f13_cleanup_retention_default_90_days():
    """purge_expired_tokens_core aplica retención D-04 (90d) por defecto."""
    from app.infrastructure.database.queries.auth.session.refresh_token_queries_core import (
        _DEFAULT_RETENTION_DAYS,
        purge_expired_tokens_core,
    )

    assert _DEFAULT_RETENTION_DAYS == 90
    with patch(
        "app.infrastructure.database.queries_async.execute_query",
        new_callable=AsyncMock,
        return_value=[{"rows_affected": 2}],
    ):
        affected = await purge_expired_tokens_core(CLIENTE_ID)
    assert affected == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f13_cleanup_v3_purges_tokens_before_sessions():
    call_order: list[str] = []

    async def _purge_tokens(*_args, **_kwargs):
        call_order.append("tokens")
        return 1

    async def _purge_sessions(*_args, **_kwargs):
        call_order.append("sessions")
        return 1

    with (
        patch(_FEATURE_FLAG, return_value=True),
        patch(_PURGE_CORE, side_effect=_purge_tokens),
        patch(_PURGE_SESSIONS, side_effect=_purge_sessions),
    ):
        await RefreshTokenCleanupJob._purge_tenant_tokens(CLIENTE_ID)

    assert call_order == ["tokens", "sessions"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f13_user_deactivate_v2_revokes_via_c03():
    with (
        patch(_FEATURE_FLAG, return_value=True),
        patch(_REVOKE_ALL_SESSIONS, new_callable=AsyncMock, return_value=2) as mock_revoke_all,
    ):
        count = await UsuarioService._revoke_user_sessions_after_lifecycle(
            CLIENTE_ID,
            USUARIO_ID,
            reason=RevokedReason.USER_DEACTIVATED,
        )

    assert count == 2
    mock_revoke_all.assert_awaited_once_with(
        usuario_id=USUARIO_ID,
        cliente_id=CLIENTE_ID,
        reason=RevokedReason.USER_DEACTIVATED,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f13_user_deactivate_v1_uses_legacy_refresh():
    with (
        patch(_FEATURE_FLAG, return_value=False),
        patch(_V1_BLACKLIST, new_callable=AsyncMock) as mock_bl,
        patch(_V1_REVOKE_ALL, new_callable=AsyncMock, return_value=4) as mock_revoke,
    ):
        count = await UsuarioService._revoke_user_sessions_after_lifecycle(
            CLIENTE_ID,
            USUARIO_ID,
            reason=RevokedReason.USER_DEACTIVATED,
        )

    assert count == 4
    mock_bl.assert_awaited_once_with(CLIENTE_ID, USUARIO_ID)
    mock_revoke.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f13_superadmin_sessions_v2_delegates_c09():
    dto = _user_session_dto()
    with (
        patch(
            "app.modules.superadmin.application.services.superadmin_usuario_service.execute_query",
            new_callable=AsyncMock,
            side_effect=[
                [{"usuario_id": USUARIO_ID, "cliente_id": CLIENTE_ID}],
            ],
        ),
        patch(_FEATURE_FLAG, return_value=True),
        patch(_C09_LIST, new_callable=AsyncMock, return_value=[dto]) as mock_list,
    ):
        result = await SuperadminUsuarioService.obtener_sesiones_usuario(
            USUARIO_ID,
            cliente_id=CLIENTE_ID,
        )

    mock_list.assert_awaited_once_with(CLIENTE_ID, USUARIO_ID)
    assert result["total_sesiones"] == 1
    sesion = result["sesiones"][0]
    assert sesion["session_id"] == SESSION_ID
    assert sesion["platform"] == "web"
    assert sesion["login_ip"] == "10.0.0.1"


@pytest.mark.unit
def test_f13_superadmin_mapper_refresh_token_info():
    dto = _user_session_dto()
    info = SuperadminUsuarioService._map_user_session_to_refresh_token_info(dto)
    assert info.session_id == SESSION_ID
    assert info.platform == "web"
    assert info.login_ip == "10.0.0.1"
    assert info.token_id == TOKEN_ID


@pytest.mark.unit
def test_f13_jwt_sid_claim_when_session_id_provided():
    token, _jti = create_access_token(
        {"sub": str(USUARIO_ID), "cliente_id": str(CLIENTE_ID)},
        session_id=SESSION_ID,
    )
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sid"] == str(SESSION_ID)


@pytest.mark.unit
def test_f13_jwt_v1_compatible_without_sid():
    token, _jti = create_access_token(
        {"sub": str(USUARIO_ID), "cliente_id": str(CLIENTE_ID)},
    )
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert "sid" not in payload
    assert payload["type"] == "access"
    assert "jti" in payload


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f13_deps_touch_business_activity_from_sid():
    from app.api.deps import _touch_business_activity_from_payload

    payload = {
        "sid": str(SESSION_ID),
        "cliente_id": str(CLIENTE_ID),
        "is_impersonation": False,
    }
    with patch(
        "app.modules.auth.application.services.business_activity_service.BusinessActivityService.touch",
        new_callable=AsyncMock,
    ) as mock_touch:
        await _touch_business_activity_from_payload(payload)

    mock_touch.assert_awaited_once_with(SESSION_ID, CLIENTE_ID)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_f13_deps_skips_impersonation_and_missing_sid():
    from app.api.deps import _touch_business_activity_from_payload

    with patch(
        "app.modules.auth.application.services.business_activity_service.BusinessActivityService.touch",
        new_callable=AsyncMock,
    ) as mock_touch:
        await _touch_business_activity_from_payload(
            {"is_impersonation": True, "sid": str(SESSION_ID), "cliente_id": str(CLIENTE_ID)}
        )
        await _touch_business_activity_from_payload({"cliente_id": str(CLIENTE_ID)})

    mock_touch.assert_not_awaited()


@pytest.mark.unit
def test_f13_regression_modules_exported():
    from app.modules.auth.application.services import BusinessActivityService as exported

    assert exported is BusinessActivityService
