"""IAM-BE-SESSIONS-P1-04-IMPL-03: cambiar_empresa_sesion con rotación atómica."""
import asyncio
from contextlib import ExitStack
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.application.session.rotate_result import RotateOutcome, RotateResult
from app.modules.auth.presentation.endpoints import refresh_access_token

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
EMPRESA_ANTERIOR = uuid4()
EMPRESA_NUEVA = uuid4()
OLD_TOKEN_ID = uuid4()
NEW_TOKEN_ID = uuid4()


def _payload(*, empresa_id=EMPRESA_ANTERIOR):
    return {
        "sub": "testuser",
        "cliente_id": str(CLIENTE_ID),
        "empresa_id": str(empresa_id),
        "empresa_selection_pending": False,
        "type": "access",
    }


def _session_out(*, access_jti="access-jti"):
    return {
        "access_token": "access",
        "refresh_token": "new-refresh",
        "access_jti": access_jti,
        "access_exp": 30,
        "user_data": {},
        "refresh_expire_days": 7,
    }


def _rotate_result(outcome: RotateOutcome, *, success: bool = False):
    return RotateResult(
        outcome=outcome,
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
        old_token_id=OLD_TOKEN_ID,
        new_token_id=NEW_TOKEN_ID if success else None,
    )


def _cambiar_patches(*, session=None, rotate_mock=None, store_mock=None, link_mock=None):
    session = session or _session_out()
    mock_context = AsyncMock(
        return_value=type(
            "Ctx",
            (),
            {"usuario_id": USUARIO_ID, "cliente_id": CLIENTE_ID, "es_activo": True},
        )()
    )
    return [
        patch(
            "app.modules.auth.application.services.auth_service.get_current_client_id",
            return_value=CLIENTE_ID,
        ),
        patch("app.core.auth.user_context.get_user_auth_context", mock_context),
        patch(
            "app.core.auth.user_context.validate_tenant_access",
            new=AsyncMock(return_value=True),
        ),
        patch.object(AuthService, "validar_empresa_para_sesion", new=AsyncMock()),
        patch(
            "app.core.tenant.empresa_preference.persist_usuario_empresa_default_id",
            new=AsyncMock(),
        ),
        patch.object(
            AuthService,
            "emitir_sesion_completa_con_empresa",
            new=AsyncMock(return_value=session),
        ),
        patch(
            "app.modules.auth.application.services.auth_service.rotate_refresh_token_service",
            rotate_mock or AsyncMock(return_value=_rotate_result(RotateOutcome.ROTATED, success=True)),
        ),
        patch(
            "app.modules.auth.application.services.auth_service.RefreshTokenService.store_refresh_token",
            store_mock or AsyncMock(return_value={"token_id": "tid"}),
        ),
        patch(
            "app.modules.auth.application.services.auth_service.RefreshTokenService.revoke_token",
            AsyncMock(),
        ),
        patch(
            "app.modules.auth.application.services.auth_service.RefreshTokenService.link_session_access_jti",
            link_mock or AsyncMock(),
        ),
        patch(
            "app.modules.auth.application.services.auth_service.AuditService.registrar_auth_event",
            new=AsyncMock(),
        ),
    ]


@pytest.mark.asyncio
async def test_cambiar_empresa_uses_rotate_not_legacy_store_revoke():
    rotate_mock = AsyncMock(return_value=_rotate_result(RotateOutcome.ROTATED, success=True))
    store_mock = AsyncMock()
    revoke_mock = AsyncMock()
    link_mock = AsyncMock()

    with ExitStack() as stack:
        for p in _cambiar_patches(rotate_mock=rotate_mock, store_mock=store_mock, link_mock=link_mock):
            stack.enter_context(p)
        stack.enter_context(
            patch(
                "app.modules.auth.application.services.auth_service.RefreshTokenService.revoke_token",
                revoke_mock,
            )
        )
        result = await AuthService.cambiar_empresa_sesion(
            payload=_payload(),
            empresa_id=EMPRESA_NUEVA,
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
            old_refresh_token="old-refresh-jwt",
        )

    assert result["refresh_token"] == "new-refresh"
    rotate_mock.assert_awaited_once()
    call_kw = rotate_mock.await_args.kwargs
    assert call_kw["old_refresh_token"] == "old-refresh-jwt"
    assert call_kw["new_refresh_token"] == "new-refresh"
    assert call_kw["empresa_id"] == EMPRESA_NUEVA
    store_mock.assert_not_awaited()
    revoke_mock.assert_not_awaited()
    link_mock.assert_awaited_once_with(NEW_TOKEN_ID, "access-jti", 30)


@pytest.mark.asyncio
async def test_cambiar_empresa_without_old_token_uses_store_legacy():
    rotate_mock = AsyncMock()
    store_mock = AsyncMock(return_value={"token_id": "tid"})

    with ExitStack() as stack:
        for p in _cambiar_patches(rotate_mock=rotate_mock, store_mock=store_mock):
            stack.enter_context(p)
        await AuthService.cambiar_empresa_sesion(
            payload=_payload(),
            empresa_id=EMPRESA_NUEVA,
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
            old_refresh_token=None,
        )

    rotate_mock.assert_not_awaited()
    store_mock.assert_awaited_once()
    assert store_mock.await_args.kwargs["is_rotation"] is True


@pytest.mark.asyncio
async def test_cambiar_empresa_idle_timeout_returns_401():
    rotate_mock = AsyncMock(return_value=_rotate_result(RotateOutcome.IDLE_TIMEOUT))

    with ExitStack() as stack:
        for p in _cambiar_patches(rotate_mock=rotate_mock):
            stack.enter_context(p)
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.cambiar_empresa_sesion(
                payload=_payload(),
                empresa_id=EMPRESA_NUEVA,
                client_type="web",
                ip_address="127.0.0.1",
                user_agent="pytest",
                old_refresh_token="old-refresh-jwt",
            )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_cambiar_empresa_already_rotated_returns_session_without_link():
    rotate_mock = AsyncMock(return_value=_rotate_result(RotateOutcome.ALREADY_ROTATED))
    link_mock = AsyncMock()

    with ExitStack() as stack:
        for p in _cambiar_patches(rotate_mock=rotate_mock, link_mock=link_mock):
            stack.enter_context(p)
        result = await AuthService.cambiar_empresa_sesion(
            payload=_payload(),
            empresa_id=EMPRESA_NUEVA,
            client_type="web",
            ip_address="127.0.0.1",
            user_agent="pytest",
            old_refresh_token="old-refresh-jwt",
        )

    assert result["access_token"] == "access"
    link_mock.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("concurrent_count", [2, 5])
async def test_concurrent_cambiar_empresa_only_one_rotation_links_jti(concurrent_count):
    rotate_calls = {"n": 0}

    async def rotate_side_effect(**kwargs):
        rotate_calls["n"] += 1
        if rotate_calls["n"] == 1:
            return _rotate_result(RotateOutcome.ROTATED, success=True)
        return _rotate_result(RotateOutcome.ALREADY_ROTATED)

    rotate_mock = AsyncMock(side_effect=rotate_side_effect)
    link_mock = AsyncMock()

    with ExitStack() as stack:
        for p in _cambiar_patches(rotate_mock=rotate_mock, link_mock=link_mock):
            stack.enter_context(p)
        results = await asyncio.gather(
            *[
                AuthService.cambiar_empresa_sesion(
                    payload=_payload(),
                    empresa_id=EMPRESA_NUEVA,
                    client_type="web",
                    ip_address="127.0.0.1",
                    user_agent="pytest",
                    old_refresh_token="old-refresh-jwt",
                )
                for _ in range(concurrent_count)
            ]
        )

    assert len(results) == concurrent_count
    assert rotate_calls["n"] == concurrent_count
    link_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_concurrent_refresh_and_cambiar_empresa_single_rotation_commit():
    """Refresh y cambiar empresa comparten rotate: solo uno persiste rotación."""
    from unittest.mock import MagicMock

    rotate_calls = {"n": 0}

    async def rotate_side_effect(**kwargs):
        rotate_calls["n"] += 1
        if rotate_calls["n"] == 1:
            return _rotate_result(RotateOutcome.ROTATED, success=True)
        return _rotate_result(RotateOutcome.ALREADY_ROTATED)

    request = MagicMock()
    request.cookies.get.return_value = "old-refresh-jwt"
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "web"
    response = MagicMock()

    refresh_patches = [
        patch("app.modules.auth.presentation.endpoints.get_client_type", return_value="web"),
        patch(
            "app.core.security.jwt.decode_refresh_token",
            return_value={"sub": "testuser", "cliente_id": str(CLIENTE_ID)},
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
            return_value={"sub": "testuser", "cliente_id": str(CLIENTE_ID)},
        ),
        patch(
            "app.modules.auth.presentation.endpoints.create_access_token",
            return_value=("access-jwt", "access-jti"),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.create_refresh_token",
            return_value=("new-refresh-jwt", "refresh-jti"),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.AuditService.registrar_auth_event",
            AsyncMock(),
        ),
    ]

    rotate_mock = AsyncMock(side_effect=rotate_side_effect)
    refresh_link = AsyncMock()
    cambiar_link = AsyncMock()

    with ExitStack() as stack:
        for p in refresh_patches:
            stack.enter_context(p)
        for p in _cambiar_patches(link_mock=cambiar_link):
            stack.enter_context(p)
        stack.enter_context(
            patch(
                "app.modules.auth.application.services.auth_service.rotate_refresh_token_service",
                rotate_mock,
            )
        )
        stack.enter_context(
            patch(
                "app.modules.auth.presentation.endpoints.rotate_refresh_token_service",
                rotate_mock,
            )
        )
        stack.enter_context(
            patch(
                "app.modules.auth.presentation.endpoints.RefreshTokenService.link_session_access_jti",
                refresh_link,
            )
        )
        await asyncio.gather(
            refresh_access_token(
                request,
                response,
                current_user={
                    "nombre_usuario": "testuser",
                    "usuario_id": USUARIO_ID,
                    "cliente_id": CLIENTE_ID,
                    "empresa_id": EMPRESA_ANTERIOR,
                },
            ),
            AuthService.cambiar_empresa_sesion(
                payload=_payload(),
                empresa_id=EMPRESA_NUEVA,
                client_type="web",
                ip_address="127.0.0.1",
                user_agent="pytest",
                old_refresh_token="old-refresh-jwt",
            ),
        )

    assert rotate_calls["n"] == 2
    assert refresh_link.await_count + cambiar_link.await_count == 1
