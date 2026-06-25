"""IAM-BE-RTR-REPLAY-WIRING-RC2 — wiring HTTP refresh V2 → motor RTR."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.application.session.rotate_result import RotateOutcome, RotateResult
from app.modules.auth.presentation.endpoints import refresh_access_token

CLIENTE_ID = uuid4()
USUARIO_ID = uuid4()
SESSION_ID = uuid4()
FAMILY_ID = uuid4()
OLD_TOKEN_ID = uuid4()
REFRESH_OLD = "old-refresh-plain"

_AUTH = "app.modules.auth.application.services.auth_service"
_FEATURE = f"{_AUTH}.is_session_v2_enabled"


def _used_token_context():
    context = MagicMock()
    context.token_row = {
        "empresa_id": None,
        "usuario_id": USUARIO_ID,
        "is_used": True,
        "is_revoked": False,
    }
    return context


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rc2_refresh_v2_depends_does_not_gate_on_get_by_hash():
    """Token is_used=1 no debe bloquearse en Depends; RTR clasifica en rotate."""
    request = MagicMock()
    request.headers = {"X-Client-Type": "web"}

    with (
        patch(
            "app.modules.auth.application.services.session_query_service.SessionQueryService.hash_token",
            return_value="b" * 64,
        ),
        patch(
            "app.modules.auth.application.services.session_query_service.SessionQueryService.get_by_hash",
            new_callable=AsyncMock,
        ) as mock_eligible,
        patch(
            "app.modules.auth.application.services.session_query_service.SessionQueryService.get_by_hash_any_state",
            new_callable=AsyncMock,
            return_value=_used_token_context(),
        ),
        patch.object(
            AuthService,
            "_fetch_user_row_for_refresh",
            new_callable=AsyncMock,
            return_value={
                "usuario_id": USUARIO_ID,
                "nombre_usuario": "user",
                "es_activo": True,
            },
        ),
    ):
        user = await AuthService._get_current_user_from_refresh_v2(
            request=request,
            refresh_token=REFRESH_OLD,
            payload={"sub": "user", "cliente_id": str(CLIENTE_ID)},
            token_cliente_id=CLIENTE_ID,
            client_type="web",
        )

    assert user["nombre_usuario"] == "user"
    mock_eligible.assert_not_awaited()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rc2_refresh_endpoint_replay_returns_401_via_rotate():
    """Replay secuencial: handler invoca rotate; COMPROMISED → 401."""
    request = MagicMock()
    request.cookies.get.return_value = REFRESH_OLD
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "pytest-agent"
    response = MagicMock()

    compromised = RotateResult(
        outcome=RotateOutcome.COMPROMISED,
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
        session_id=SESSION_ID,
        family_id=FAMILY_ID,
        old_token_id=OLD_TOKEN_ID,
    )

    with (
        patch(
            "app.modules.auth.presentation.endpoints.get_client_type",
            return_value="web",
        ),
        patch(
            "app.core.security.jwt.decode_refresh_token",
            return_value={
                "sub": "user",
                "cliente_id": str(CLIENTE_ID),
                "is_impersonation": False,
            },
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
            return_value={"sub": "user", "cliente_id": str(CLIENTE_ID)},
        ),
        patch(
            "app.modules.auth.presentation.endpoints.create_refresh_token",
            return_value=("new-refresh-jwt", "refresh-jti"),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.AuthService.rotate_refresh_session",
            AsyncMock(return_value=compromised),
        ) as mock_rotate,
        patch(
            "app.modules.auth.presentation.endpoints.create_access_token",
        ) as mock_access,
    ):
        with pytest.raises(HTTPException) as exc:
            await refresh_access_token(
                request,
                response,
                current_user={
                    "nombre_usuario": "user",
                    "usuario_id": USUARIO_ID,
                    "cliente_id": CLIENTE_ID,
                    "empresa_id": None,
                },
            )

    assert exc.value.status_code == 401
    mock_rotate.assert_awaited_once()
    mock_access.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rc2_refresh_endpoint_valid_rotate_unchanged():
    """Refresh válido sigue emitiendo access tras ROTATED."""
    request = MagicMock()
    request.cookies.get.return_value = REFRESH_OLD
    request.client.host = "127.0.0.1"
    request.headers.get.return_value = "pytest-agent"
    response = MagicMock()

    rotated = RotateResult(
        outcome=RotateOutcome.ROTATED,
        cliente_id=CLIENTE_ID,
        usuario_id=USUARIO_ID,
        session_id=SESSION_ID,
        new_token_id=uuid4(),
    )

    with (
        patch(
            "app.modules.auth.presentation.endpoints.get_client_type",
            return_value="web",
        ),
        patch(
            "app.core.security.jwt.decode_refresh_token",
            return_value={
                "sub": "user",
                "cliente_id": str(CLIENTE_ID),
                "sid": str(SESSION_ID),
                "is_impersonation": False,
            },
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
            return_value={"sub": "user", "cliente_id": str(CLIENTE_ID)},
        ),
        patch(
            "app.modules.auth.presentation.endpoints.create_refresh_token",
            return_value=("new-refresh-jwt", "refresh-jti"),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.AuthService.rotate_refresh_session",
            AsyncMock(return_value=rotated),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.create_access_token",
            return_value=("access-jwt", "access-jti"),
        ),
        patch(
            "app.modules.auth.presentation.endpoints.AuditService.registrar_auth_event",
            AsyncMock(),
        ),
    ):
        result = await refresh_access_token(
            request,
            response,
            current_user={
                "nombre_usuario": "user",
                "usuario_id": USUARIO_ID,
                "cliente_id": CLIENTE_ID,
                "empresa_id": None,
            },
        )

    assert result["access_token"] == "access-jwt"
    response.set_cookie.assert_called_once()
