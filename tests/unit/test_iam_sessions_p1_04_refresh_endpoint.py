"""IAM-BE-SESSIONS-P1-04-IMPL-02: /auth/refresh con rotación atómica."""
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.application.session.rotate_result import RotateOutcome, RotateResult
from app.modules.auth.presentation.endpoints import (
    get_current_user_for_refresh_endpoint,
    refresh_access_token,
)

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
OLD_TOKEN_ID = uuid4()
NEW_TOKEN_ID = uuid4()


def _current_user():
    return {
        "nombre_usuario": "admin",
        "usuario_id": USUARIO_ID,
        "cliente_id": CLIENTE_ID,
        "empresa_id": None,
    }


def _rotate_result(outcome: RotateOutcome, *, success: bool = False):
    return RotateResult(
        outcome=outcome,
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
        old_token_id=OLD_TOKEN_ID,
        new_token_id=NEW_TOKEN_ID if success else None,
    )


@pytest.mark.asyncio
async def test_refresh_endpoint_uses_rotate_not_legacy_store_revoke():
    request = MagicMock()
    request.cookies.get.return_value = "old-refresh-jwt"
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "web"
    response = MagicMock()

    mock_rotate = AsyncMock(
        return_value=_rotate_result(RotateOutcome.ROTATED, success=True)
    )
    mock_link = AsyncMock()

    with patch(
        "app.modules.auth.presentation.endpoints.get_client_type",
        return_value="web",
    ), patch(
        "app.core.security.jwt.decode_refresh_token",
        return_value={"sub": "admin", "cliente_id": str(CLIENTE_ID), "is_impersonation": False},
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.resolve_level_info_for_token_refresh",
        AsyncMock(return_value={"access_level": 1, "is_super_admin": False, "user_type": "user"}),
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.usuario_tiene_es_admin_cliente",
        AsyncMock(return_value=False),
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.get_token_expiration_for_cliente",
        AsyncMock(return_value={"access_token_minutes": 30, "refresh_token_days": 7}),
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.resolve_requires_password_change",
        return_value=False,
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.build_token_data_from_level_info",
        return_value={"sub": "admin", "cliente_id": str(CLIENTE_ID)},
    ), patch(
        "app.modules.auth.presentation.endpoints.create_access_token",
        return_value=("access-jwt", "access-jti"),
    ), patch(
        "app.modules.auth.presentation.endpoints.create_refresh_token",
        return_value=("new-refresh-jwt", "refresh-jti"),
    ), patch(
        "app.modules.auth.presentation.endpoints.rotate_refresh_token_service",
        mock_rotate,
    ), patch(
        "app.modules.auth.presentation.endpoints.RefreshTokenService.store_refresh_token",
        AsyncMock(),
    ) as mock_store, patch(
        "app.modules.auth.presentation.endpoints.RefreshTokenService.revoke_token",
        AsyncMock(),
    ) as mock_revoke, patch(
        "app.modules.auth.presentation.endpoints.RefreshTokenService.link_session_access_jti",
        mock_link,
    ), patch(
        "app.modules.auth.presentation.endpoints.AuditService.registrar_auth_event",
        AsyncMock(),
    ):
        result = await refresh_access_token(
            request, response, current_user=_current_user()
        )

    assert result["access_token"] == "access-jwt"
    mock_rotate.assert_awaited_once()
    mock_store.assert_not_awaited()
    mock_revoke.assert_not_awaited()
    mock_link.assert_awaited_once_with(NEW_TOKEN_ID, "access-jti", access_expire_minutes=30)
    response.set_cookie.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_endpoint_idle_timeout_returns_401():
    request = MagicMock()
    request.cookies.get.return_value = "old-refresh-jwt"
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "web"
    response = MagicMock()

    with patch(
        "app.modules.auth.presentation.endpoints.get_client_type",
        return_value="web",
    ), patch(
        "app.core.security.jwt.decode_refresh_token",
        return_value={"sub": "admin", "cliente_id": str(CLIENTE_ID)},
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.resolve_level_info_for_token_refresh",
        AsyncMock(return_value={"access_level": 1, "is_super_admin": False, "user_type": "user"}),
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.usuario_tiene_es_admin_cliente",
        AsyncMock(return_value=False),
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.get_token_expiration_for_cliente",
        AsyncMock(return_value={"access_token_minutes": 30, "refresh_token_days": 7}),
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.resolve_requires_password_change",
        return_value=False,
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.build_token_data_from_level_info",
        return_value={"sub": "admin"},
    ), patch(
        "app.modules.auth.presentation.endpoints.create_access_token",
        return_value=("access-jwt", "access-jti"),
    ), patch(
        "app.modules.auth.presentation.endpoints.create_refresh_token",
        return_value=("new-refresh-jwt", "refresh-jti"),
    ), patch(
        "app.modules.auth.presentation.endpoints.rotate_refresh_token_service",
        AsyncMock(return_value=_rotate_result(RotateOutcome.IDLE_TIMEOUT)),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await refresh_access_token(
                request, response, current_user=_current_user()
            )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_endpoint_already_rotated_skips_cookie_update():
    request = MagicMock()
    request.cookies.get.return_value = "old-refresh-jwt"
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "web"
    response = MagicMock()

    with patch(
        "app.modules.auth.presentation.endpoints.get_client_type",
        return_value="web",
    ), patch(
        "app.core.security.jwt.decode_refresh_token",
        return_value={"sub": "admin", "cliente_id": str(CLIENTE_ID)},
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.resolve_level_info_for_token_refresh",
        AsyncMock(return_value={"access_level": 1, "is_super_admin": False, "user_type": "user"}),
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.usuario_tiene_es_admin_cliente",
        AsyncMock(return_value=False),
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.get_token_expiration_for_cliente",
        AsyncMock(return_value={"access_token_minutes": 30, "refresh_token_days": 7}),
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.resolve_requires_password_change",
        return_value=False,
    ), patch(
        "app.modules.auth.presentation.endpoints.AuthService.build_token_data_from_level_info",
        return_value={"sub": "admin"},
    ), patch(
        "app.modules.auth.presentation.endpoints.create_access_token",
        return_value=("access-jwt", "access-jti"),
    ), patch(
        "app.modules.auth.presentation.endpoints.create_refresh_token",
        return_value=("new-refresh-jwt", "refresh-jti"),
    ), patch(
        "app.modules.auth.presentation.endpoints.rotate_refresh_token_service",
        AsyncMock(return_value=_rotate_result(RotateOutcome.ALREADY_ROTATED)),
    ), patch(
        "app.modules.auth.presentation.endpoints.RefreshTokenService.link_session_access_jti",
        AsyncMock(),
    ) as mock_link, patch(
        "app.modules.auth.presentation.endpoints.AuditService.registrar_auth_event",
        AsyncMock(),
    ):
        result = await refresh_access_token(
            request, response, current_user=_current_user()
        )

    assert result["access_token"] == "access-jwt"
    response.set_cookie.assert_not_called()
    mock_link.assert_not_awaited()


@pytest.mark.asyncio
async def test_refresh_depends_suppresses_session_rotated_reuse():
    request = MagicMock()
    with patch.object(
        AuthService,
        "get_current_user_from_refresh",
        AsyncMock(return_value=_current_user()),
    ) as mock_get:
        await get_current_user_for_refresh_endpoint(
            request,
            refresh_token_cookie="cookie-token",
            body=MagicMock(refresh_token=None),
        )
    mock_get.assert_awaited_once_with(
        request,
        "cookie-token",
        None,
        suppress_session_rotated_reuse=True,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("concurrent_count", [2, 5, 10])
async def test_concurrent_refresh_only_one_rotation_commits_refresh(concurrent_count):
    """
    Simula N refresh simultáneos: solo uno rota; el resto already_rotated.
    Verifica una sola llamada con éxito de rotación (un token activo en BD).
    """
    request = MagicMock()
    request.cookies.get.return_value = "old-refresh-jwt"
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "web"
    response = MagicMock()

    rotate_calls = {"n": 0}

    async def rotate_side_effect(**kwargs):
        rotate_calls["n"] += 1
        if rotate_calls["n"] == 1:
            return _rotate_result(RotateOutcome.ROTATED, success=True)
        return _rotate_result(RotateOutcome.ALREADY_ROTATED)

    common_patches = [
        patch("app.modules.auth.presentation.endpoints.get_client_type", return_value="web"),
        patch(
            "app.core.security.jwt.decode_refresh_token",
            return_value={"sub": "admin", "cliente_id": str(CLIENTE_ID)},
        ),
        patch(
            "app.modules.auth.presentation.endpoints.AuthService.resolve_level_info_for_token_refresh",
            AsyncMock(return_value={"access_level": 1, "is_super_admin": False, "user_type": "user"}),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.AuthService.usuario_tiene_es_admin_cliente",
            AsyncMock(return_value=False),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.AuthService.get_token_expiration_for_cliente",
            AsyncMock(return_value={"access_token_minutes": 30, "refresh_token_days": 7}),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.AuthService.resolve_requires_password_change",
            return_value=False,
        ),
        patch(
            "app.modules.auth.presentation.endpoints.AuthService.build_token_data_from_level_info",
            return_value={"sub": "admin"},
        ),
        patch(
            "app.modules.auth.presentation.endpoints.create_access_token",
            return_value=("access-jwt", "access-jti"),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.create_refresh_token",
            side_effect=lambda **kw: (f"new-{uuid4()}", "refresh-jti"),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.rotate_refresh_token_service",
            AsyncMock(side_effect=rotate_side_effect),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.AuditService.registrar_auth_event",
            AsyncMock(),
        ),
    ]

    from contextlib import ExitStack

    link_mock = AsyncMock()
    cookie_mocks = [MagicMock() for _ in range(concurrent_count)]

    with ExitStack() as stack:
        for p in common_patches:
            stack.enter_context(p)
        stack.enter_context(
            patch(
                "app.modules.auth.presentation.endpoints.RefreshTokenService.link_session_access_jti",
                link_mock,
            )
        )
        results = await asyncio.gather(
            *[
                refresh_access_token(
                    request, cookie_mocks[i], current_user=_current_user()
                )
                for i in range(concurrent_count)
            ]
        )

    assert len(results) == concurrent_count
    assert rotate_calls["n"] == concurrent_count
    link_mock.assert_awaited_once()
    assert sum(1 for m in cookie_mocks if m.set_cookie.called) == 1


def test_empresa_cambiar_uses_atomic_rotate_not_legacy_revoke():
    import app.modules.auth.application.services.auth_service as auth_mod

    source = open(auth_mod.__file__, encoding="utf-8").read()
    assert "rotate_refresh_token_service" in source
    cambiar_block = source.split("async def cambiar_empresa_sesion", 1)[1].split(
        "async def _extract_refresh_token_for_logout", 1
    )[0]
    assert "rotate_refresh_token_service" in cambiar_block
    assert "revoke_token" not in cambiar_block
