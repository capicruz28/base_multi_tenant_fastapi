"""IAM-BE-ME-SESSION-PROBE-WIRING-01 — probe gate GET /auth/me."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.deps_auth import require_active_password_session_v2_for_me
from app.modules.auth.application.session.session_probe_result import SessionProbeResult

CLIENTE_ID = uuid4()
SESSION_ID = uuid4()
REFRESH = "refresh-jwt-value"


def _payload(*, impersonation: bool = False, selection_pending: bool = False):
    data = {
        "sub": "admin",
        "cliente_id": str(CLIENTE_ID),
        "empresa_id": str(uuid4()),
    }
    if impersonation:
        data["is_impersonation"] = True
    if selection_pending:
        data["empresa_selection_pending"] = True
    return data


def _request(*, refresh_cookie: str | None = REFRESH):
    request = MagicMock()
    request.headers.get.return_value = "web"
    request.cookies.get.return_value = refresh_cookie
    return request


@pytest.mark.asyncio
async def test_me_probe_rejects_inactive_session_v2():
    probe = SessionProbeResult(
        current_session_id=SESSION_ID,
        is_active=False,
    )
    with patch(
        "app.modules.auth.application.session.session_v2_feature.is_session_v2_enabled",
        return_value=True,
    ), patch(
        "app.modules.auth.application.services.session_probe_service.SessionProbeService.resolve_context",
        new_callable=AsyncMock,
        return_value=probe,
    ):
        with pytest.raises(HTTPException) as exc:
            await require_active_password_session_v2_for_me(
                request=_request(),
                payload=_payload(),
            )
    assert exc.value.status_code == 401
    assert "Sesión expirada o cerrada remotamente" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_me_probe_allows_active_session_v2():
    probe = SessionProbeResult(
        current_session_id=SESSION_ID,
        is_active=True,
    )
    with patch(
        "app.modules.auth.application.session.session_v2_feature.is_session_v2_enabled",
        return_value=True,
    ), patch(
        "app.modules.auth.application.services.session_probe_service.SessionProbeService.resolve_context",
        new_callable=AsyncMock,
        return_value=probe,
    ):
        result = await require_active_password_session_v2_for_me(
            request=_request(),
            payload=_payload(),
        )
    assert result["sub"] == "admin"


@pytest.mark.asyncio
async def test_me_probe_skips_when_v2_flag_off():
    with patch(
        "app.modules.auth.application.session.session_v2_feature.is_session_v2_enabled",
        return_value=False,
    ), patch(
        "app.modules.auth.application.services.session_probe_service.SessionProbeService.resolve_context",
        new_callable=AsyncMock,
    ) as mock_probe:
        await require_active_password_session_v2_for_me(
            request=_request(),
            payload=_payload(),
        )
    mock_probe.assert_not_awaited()


@pytest.mark.asyncio
async def test_me_probe_skips_impersonation():
    with patch(
        "app.modules.auth.application.session.session_v2_feature.is_session_v2_enabled",
        return_value=True,
    ), patch(
        "app.modules.auth.application.services.session_probe_service.SessionProbeService.resolve_context",
        new_callable=AsyncMock,
    ) as mock_probe:
        await require_active_password_session_v2_for_me(
            request=_request(),
            payload=_payload(impersonation=True),
        )
    mock_probe.assert_not_awaited()


@pytest.mark.asyncio
async def test_me_probe_fail_soft_without_refresh_cookie():
    with patch(
        "app.modules.auth.application.session.session_v2_feature.is_session_v2_enabled",
        return_value=True,
    ), patch(
        "app.modules.auth.application.services.session_probe_service.SessionProbeService.resolve_context",
        new_callable=AsyncMock,
    ) as mock_probe:
        result = await require_active_password_session_v2_for_me(
            request=_request(refresh_cookie=None),
            payload=_payload(),
        )
    mock_probe.assert_not_awaited()
    assert result["sub"] == "admin"


@pytest.mark.asyncio
async def test_me_probe_fail_soft_empty_probe_result():
    with patch(
        "app.modules.auth.application.session.session_v2_feature.is_session_v2_enabled",
        return_value=True,
    ), patch(
        "app.modules.auth.application.services.session_probe_service.SessionProbeService.resolve_context",
        new_callable=AsyncMock,
        return_value=SessionProbeResult(),
    ):
        result = await require_active_password_session_v2_for_me(
            request=_request(),
            payload=_payload(),
        )
    assert result["sub"] == "admin"
